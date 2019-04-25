from copy import deepcopy
import traceback
import json
import hashlib
import time
import os
import subprocess
import tempfile
import sys
import shutil
import fnmatch
import inspect
import shlex
from mountainclient import client as mt
from mountainclient import MountainClient
import datetime
from .shellscript import ShellScript
from .temporarydirectory import TemporaryDirectory
import mtlogging
import numpy as np

local_client = MountainClient()

class MountainJob():
    def __init__(self, *, processor=None, job_object=None):
        if processor and (job_object is None):
            raise Exception('Use createJob() or createJobs() to create MountainJob objects.')
        self.result=None
        self._processor=processor
        self._job_object=deepcopy(job_object)
        self._use_cached_results_only=False

    def isNull(self):
        return (self._job_object is None)

    def getObject(self):
        return deepcopy(self._job_object)

    def addFilesToRealize(self, files_to_realize):
        if self._job_object is None:
            return
        if type(files_to_realize)==str:
            self._job_object['additional_files_to_realize'].append(files_to_realize)
        elif type(files_to_realize)==list:
            self._job_object['additional_files_to_realize'].extend(files_to_realize)
        else:
            raise Exception('Unexpected type of files_to_realize in addFilesToRealize')

    def getFilesToRealize(self):
        if self._job_object is None:
            return []
        # These are the files needed at the compute location to actually run the job
        ret=[]
        if self._job_object['container']:
            ret.append(self._job_object['container'])
        for input0 in self._job_object['inputs'].values():
            if not input0.get('directory', False):
                ret.append(input0['path'])
        if self._job_object['processor_code']:
            ret.append(self._job_object['processor_code'])
        if 'additional_files_to_realize' in self._job_object:
            ret.extend(self._job_object['additional_files_to_realize'])
        return ret

    def useRemoteUrlsForInputFiles(self):
        if self._job_object is None:
            return
        if self._job_object['container']:
            self._job_object['container'] = _make_remote_url_for_file(self._job_object['container'])
        for input_name, input0 in self._job_object['inputs'].items():
            if not input0.get('directory', False):
                self._job_object['inputs'][input_name]['path'] = _make_remote_url_for_file(input0['path'])
        if 'additional_files_to_realize' in self._job_object:
            for ii, fname in enumerate(self._job_object['additional_files_to_realize']):
                self._job_object['additional_files_to_realize'][ii] = _make_remote_url_for_file(fname)

    def setUseCachedResultsOnly(self, val):
        self._use_cached_results_only = val

    def storeResultInCache(self, result):
        self._store_result_in_cache(result)

    @mtlogging.log(name='MountainJob:execute')
    def execute(self):
        if self._job_object is None:
            return MountainJobResult()
        container = self._job_object['container']
        force_run = self._job_object['force_run']
        use_cache = self._job_object['use_cache']
        keep_temp_files = self._job_object['keep_temp_files']
        job_timeout = self._job_object.get('timeout', None)
        label = self._job_object.get('label', '')
        ignore_local_cache = (os.environ.get('MLPROCESSORS_IGNORE_LOCAL_CACHE', 'FALSE') == 'TRUE')

        if (use_cache) and (not force_run) and (not ignore_local_cache):
            result = self._find_result_in_cache()
            if result:
                self._copy_outputs_from_result_to_dest_paths(result)
                return self._post_process_result(result)

        if self._use_cached_results_only:
            return None

        keep_temp_files=True
        with TemporaryDirectory(remove=(not keep_temp_files), prefix='tmp_execute_outputdir_'+self._job_object['processor_name']) as tmp_output_path:
            attributes_for_processor = dict()
            tmp_output_file_names = dict()
            output_files_to_copy = []
            output_files = dict()
            inputs_to_bind = []
            tmp_process_console_out_fname = os.path.join(tmp_output_path, 'process_console_out.txt')
            tmp_process_console_out_fname_in_container = os.path.join('/processor_outputs', 'process_console_out.txt')
            for input_name, input0 in self._job_object['inputs'].items():
                if not input0.get('directory', False):
                    if input0['path']:
                        input_value = self._realize_input(input0['path'])
                        if not input_value:
                            raise Exception('Unable to realize input {}: {}'.format(input_name, input0['path']))
                    else:
                        if (not container) and self._processor:
                            # running directly so we are okay with an input object
                            input_value = input0['object']
                        else:
                            raise Exception('Cannot run job indirectly with input {} that is not a file'.format(input_name))
                else:
                    input_value = input0['path']
                if not container:
                    attributes_for_processor[input_name] = input_value
                else:
                    ext = _get_file_ext(input_value) or '.in'
                    
                    if input0.get('directory', False) and (input0['path'].startswith('kbucket://') or input0['path'].startswith('sha1dir://')):
                        infile_in_container = input0['path']
                    else:
                        infile_in_container = '/processor_inputs/{}{}'.format(input_name, ext)
                        inputs_to_bind.append((input_value, infile_in_container))
                    attributes_for_processor[input_name] = infile_in_container
            for output_name, output_value in self._job_object['outputs'].items():
                if type(output_value)==str:
                    file_ext = _get_file_ext(output_value) or '.out'
                elif type(output_value)==dict:
                    file_ext = output_value.get('ext', '.out')
                else:
                    raise Exception('Unexpected type for output value {}: {}'.format(output_name, type(output_value)))
                tmp_output_fname = os.path.join(tmp_output_path, output_name+file_ext)
                tmp_output_file_names[output_name] = tmp_output_fname
                if type(output_value)==str:
                    output_fname=output_value
                    output_files_to_copy.append((tmp_output_fname, output_fname))
                    output_files[output_name] = output_fname
                elif type(output_value)==dict:
                    if output_value.get('dest_path', None):
                        output_fname = output_value['dest_path']
                        output_files_to_copy.append((tmp_output_fname, output_fname))
                        output_files[output_name] = output_fname
                    else:
                        output_files[output_name] = tmp_output_fname
                else:
                    raise Exception('Unexpected type for output value {}: {}'.format(output_name, type(output_value)))
                if not container:
                   attributes_for_processor[output_name] = tmp_output_fname
                else:
                    tmp_output_fname_in_container = os.path.join('/processor_outputs', output_name+file_ext)
                    attributes_for_processor[output_name] = tmp_output_fname_in_container
            for param_name, param_value in self._job_object['parameters'].items():
                attributes_for_processor[param_name] = param_value

            runtime_capture = ConsoleCapture()
            runtime_capture.start_capturing()
            print('Job: {}'.format(label))
            print('Timestamp: {:%Y-%m-%d %H:%M:%S}'.format(datetime.datetime.now()))
            R = MountainJobResult()
            if (not container) and self._processor:
                # This means we can just run it directly
                X = self._processor()  # instance
                for attr_name, attr_val in attributes_for_processor.items():
                    setattr(X, attr_name, attr_val)
                try:
                    print('Running processor directly...')
                    mtlogging.sublog('running-directly')
                    X.run()
                    mtlogging.sublog(None)
                    retcode = 0
                except:
                    traceback.print_exc()
                    runtime_capture.stop_capturing()
                    R.retcode = -1
                    R.runtime_info = runtime_capture.runtimeInfo()
                    R.console_out = local_client.saveText(text = runtime_capture.consoleOut(), basename='console_out.txt')
                    return R
            else:
                # Otherwise we need to do code generation
                timer = time.time()
                with TemporaryDirectory(remove=(not keep_temp_files), prefix='tmp_execute_'+self._job_object['processor_name']) as temp_path:
                    self._generate_execute_code(temp_path, attributes_for_processor=attributes_for_processor)

                    run_sh_script = ShellScript("""
                        #!/bin/bash
                        set -e
                        {env_vars}
                        python3 {temp_path}/run.py > {console_out_fname} 2>&1
                    """, script_path=os.path.join(temp_path, 'run.sh'))

                    if not container:
                        run_sh_script.substitute('{temp_path}', temp_path)
                        run_sh_script.substitute('{console_out_fname}', tmp_process_console_out_fname)
                        run_sh_script.substitute('{env_vars}', '')
                        shell_script=run_sh_script
                    else:
                        print('Realizing container file: {}'.format(container))
                        container_orig = container
                        container = mt.realizeFile(container)
                        if not container:
                            raise Exception('Unable to realize container file: {}'.format(container_orig))
                        singularity_opts, env_vars = _get_singularity_opts_and_env_vars()
                        singularity_opts.append('-B {}:{}'.format(temp_path, '/run_in_container'))
                        singularity_opts.append('-B {}:{}'.format(tmp_output_path, '/processor_outputs'))
                        source_path=os.path.dirname(os.path.realpath(__file__))
                        singularity_opts.append('-B {}:/python/mountaintools'.format(os.path.abspath(os.path.join(source_path, '..'))))
                        for tobind in inputs_to_bind:
                            singularity_opts.append('-B {}:{}'.format(tobind[0], tobind[1]))
                        environment_variables = self._job_object.get('environment_variables', [])
                        for v in environment_variables:
                            val = os.environ.get(v, '')
                            if val:
                                env_vars.append('{}={}'.format(v, val))
                        env_vars.append('PYTHONPATH=/python/mountaintools')
                        
                        run_sh_script.substitute('{temp_path}', '/run_in_container')
                        run_sh_script.substitute('{console_out_fname}', tmp_process_console_out_fname_in_container)
                        run_sh_script.substitute('{env_vars}', '\n'.join(['export '+env_var for env_var in env_vars]))
                        run_sh_script.write()

                        singularity_sh_script = ShellScript("""
                            #!/bin/bash
                            set -e

                            singularity exec {singularity_opts} {container} {temp_path}/run.sh
                        """, script_path=os.path.join(temp_path, 'singularity_run.sh'))
                        singularity_sh_script.substitute('{temp_path}', '/run_in_container')
                        singularity_sh_script.substitute('{singularity_opts}', ' '.join(singularity_opts))
                        singularity_sh_script.substitute('{container}', container)

                        shell_script = singularity_sh_script

                    mtlogging.sublog('running-script')
                    shell_script.start()
                    while shell_script.isRunning():
                        shell_script.wait(5)
                        if job_timeout:
                            if shell_script.elapsedTimeSinceStart() > job_timeout:
                                print('Elapsed time exceeded timeout for process: {} > {} sec'.format(shell_script.elapsedTimeSinceStart(), job_timeout))
                                R.timed_out = True
                                shell_script.stop()
                    retcode = shell_script.returnCode()
                    mtlogging.sublog(None)

                if os.path.exists(tmp_process_console_out_fname):
                    process_console_out = _read_text_file(tmp_process_console_out_fname) or ''
                    if process_console_out:
                        lines0=process_console_out.splitlines()
                        for line0 in lines0:
                            print('>> {}'.format(line0))
                    else:
                        print('>> No console out for process')
                else:
                    print('WARNING: no process console out file found: '+tmp_process_console_out_fname)
                elapsed = time.time() - timer
                print('========== {} exited with code {} after {} sec'.format(self._job_object['processor_name'], retcode, elapsed))
                print('================================================================================')
            
            runtime_capture.stop_capturing()
            R.retcode = retcode
            R.runtime_info = runtime_capture.runtimeInfo()
            R.console_out = local_client.saveText(text = runtime_capture.consoleOut(), basename='console_out.txt')
            R.outputs=dict()
            if retcode == 0:
                for output_tocopy in output_files_to_copy:
                    print('Saving output: {} -> {}'.format(output_tocopy[0], output_tocopy[1]))
                    shutil.copyfile(output_tocopy[0], output_tocopy[1])
                for output_name, fname in output_files.items():
                    if not os.path.exists(fname):
                        raise Exception('Unexpected: output file {} does not exist: {}'.format(output_name, fname), os.path.exists(fname))
                    R.outputs[output_name] = local_client.saveFile(path=fname)

            if (retcode == 0) and use_cache:
                self._store_result_in_cache(R)

            return self._post_process_result(R)

    def _post_process_result(self, R):
        output_names = R.outputs.keys()
        for output_name in output_names:
            out_fname = R.outputs[output_name]
            out_obj = self._job_object['outputs'][output_name]
            if type(out_obj) != dict:
                out_obj = dict()
            if out_obj.get('is_array', False):
                out_fname = mt.realizeFile(out_fname)
                try:
                    R.outputs[output_name] = np.load(out_fname)
                except:
                    print('Error loading output array', output_name, out_fname)
                    R.retcode == -1
        return R

    def _realize_input(self, fname):
        if fname.startswith('kbucket://') or fname.startswith('sha1dir://'):
            if local_client.findFile(fname):
                return mt.realizeFile(fname)
            else:
                # must be a directory
                return fname
        else:
            return mt.realizeFile(fname)

    def _generate_execute_code(self, temp_path, attributes_for_processor):
        if not self._job_object['processor_code']:
            raise Exception('Processor code is missing for job', self._job_object.get('processor_name'))
        code = mt.loadObject(path = self._job_object['processor_code'])
        if code is None:
            raise Exception('Unable to load processor code for job: {}'.format(self._job_object['processor_code']))
        _write_python_code_to_directory(temp_path+'/processor_source', code)
        
        processor_class_name = self._job_object['processor_class_name']

        run_py_script = ShellScript("""
            #!/usr/bin/env python

            from processor_source import {processor_class_name}
            import sys

            def main():
                print('Running processor (class={processor_class_name}) ...')
                X = {processor_class_name}()
            {set_attributes}
                X.run()

            if __name__ == "__main__":
                try:
                    main()
                except:
                    sys.stdout.flush()
                    sys.stderr.flush()
                    raise
        """)
        
        set_attributes_code = []
        for attr_name, attr_val in attributes_for_processor.items():
            set_attributes_code.append(
                "    setattr(X, '{}', {})".format(attr_name, _code_generate_value(attr_val))
            )
        set_attributes_code = '\n'.join(set_attributes_code)

        run_py_script.substitute('{processor_class_name}', processor_class_name)
        run_py_script.substitute('{set_attributes}', set_attributes_code)

        run_py_script.write(os.path.join(temp_path, 'run.py'))

    def _find_result_in_cache(self):
        output_paths = dict()
        for output_name, output0 in self._job_object['outputs'].items():
            signature0 = output0['signature']
            output_path = local_client.getValue(key=signature0, check_alt=True)
            if not output_path:
                return None
            output_paths[output_name] = output_path
        
        runtime_info_signature = self._job_object['runtime_info_signature']
        output_paths['--runtime-info--'] = local_client.getValue(key=runtime_info_signature, check_alt=True)
        if not output_paths['--runtime-info--']:
            return None

        console_out_signature = self._job_object['console_out_signature']
        output_paths['--console-out--'] = local_client.getValue(key=console_out_signature, check_alt=True)
        if not output_paths['--console-out--']:
            return None
    
        for output_name in output_paths.keys():
            orig_path = output_paths[output_name]
            output_paths[output_name] = local_client.realizeFile(output_paths[output_name])
            if not output_paths[output_name]:
                print('Unable to realize cached output', output_name, orig_path)
                return None
            
        runtime_info = local_client.loadObject(path=output_paths['--runtime-info--'])
        if runtime_info is None:
            print('Unable to load cached runtime info', output_paths['--runtime-info--'])
            return None

        console_out_text = local_client.loadText(path=output_paths['--console-out--'])
        if console_out_text is None:
            print('Unable to load cached console out text:', output_paths['--console-out--'])
            return None
        
        R = MountainJobResult()
        R.retcode=0
        R.runtime_info = runtime_info
        R.console_out = local_client.saveFile(path=output_paths['--console-out--'])
        R.outputs=dict()
        for output_name in self._job_object['outputs'].keys():
            R.outputs[output_name] = local_client.saveFile(path=output_paths[output_name])
        return R

    def _store_result_in_cache(self, result):
        for output_name, output0 in self._job_object['outputs'].items():
            output_path = local_client.getSha1Url(result.outputs[output_name])
            if output_path:
                local_client.setValue(key=output0['signature'], value=output_path)
            else:
                raise Exception('Unable to store output in cache', output_name, result.outputs[output_name])

        runtime_info_signature = self._job_object['runtime_info_signature']
        runtime_info_path = local_client.saveObject(object=result.runtime_info)
        local_client.setValue(key=runtime_info_signature, value=runtime_info_path)

        console_out_signature = self._job_object['console_out_signature']
        console_out_path = result.console_out
        local_client.setValue(key=console_out_signature, value=console_out_path)

    def _copy_outputs_from_result_to_dest_paths(self, result):
        for output_name, output0 in self._job_object['outputs'].items():
            if type(output0) == str:
                dest_path = output0
            elif type(output0)==dict:
                if output0.get('dest_path', None):
                    dest_path = output0['dest_path']
                else:
                    dest_path = None
            else:
                dest_path = None
            if dest_path:
                local_client.realizeFile(result.outputs[output_name], dest_path=dest_path)
                result.outputs[output_name] = dest_path

class MountainJobResult():
    def __init__(self, result_object=None):
        self.retcode = 0
        self.timed_out = False
        self.console_out = None
        self.runtime_info = None
        self.outputs = None
        if result_object is not None:
            self.fromObject(result_object)
    def getObject(self):
        return dict(
            retcode=self.retcode,
            timed_out=self.timed_out,
            console_out=self.console_out,
            runtime_info=deepcopy(self.runtime_info),
            outputs=deepcopy(self.outputs)
        )
    def fromObject(self, obj):
        self.retcode = obj['retcode']
        self.timed_out = obj.get('timed_out', False)
        self.console_out = obj['console_out']
        self.runtime_info = deepcopy(obj['runtime_info'])
        self.outputs = deepcopy(obj['outputs'])

class Logger2(object):
    def __init__(self, file1, file2):
        self.file1 = file1
        self.file2 = file2

    def write(self, data):
        self.file1.write(data)
        self.file2.write(data)

    def flush(self):
        self.file1.flush()
        self.file2.flush()

class ConsoleCapture():
    def __init__(self):
        self._console_out = ''
        self._tmp_fname = None
        self._file_handle = None
        self._time_start = None
        self._time_stop = None
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def start_capturing(self):
        self._tmp_fname = tempfile.mktemp(suffix='.txt')
        self._file_handle = open(self._tmp_fname, 'w')
        sys.stdout = Logger2(self._file_handle, self._original_stdout)
        sys.stderr = Logger2(self._file_handle, self._original_stderr)
        self._time_start = time.time()

    def stop_capturing(self):
        self._time_stop = time.time()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self._file_handle.close()
        with open(self._tmp_fname, 'r') as f:
            self._console_out = f.read()
        os.unlink(self._tmp_fname)

    def addToConsoleOut(self, txt):
        self._file_handle.write(txt)

    def runtimeInfo(self):
        return dict(
            start_time = self._time_start - 0,
            end_time = self._time_stop - 0,
            elapsed_sec = self._time_stop - self._time_start
        )

    def consoleOut(self):
        return self._console_out

def _write_python_code_to_directory(dirname, code):
    if os.path.exists(dirname):
        raise Exception(
            'Cannot write code to already existing directory: {}'.format(dirname))
    os.mkdir(dirname)
    for item in code['files']:
        fname0 = dirname+'/'+item['name']
        with open(fname0, 'w') as f:
            f.write(item['content'])
    for item in code['dirs']:
        _write_python_code_to_directory(
            dirname+'/'+item['name'], item['content'])

def _code_generate_value(val):
    if type(val) == str:
        return "'{}'".format(val)
    elif type(val) == dict:
        return "{}".format(json.dumps(val))
    else:
        return val

def _get_singularity_opts_and_env_vars():
    singularity_opts = []
    kbucket_cache_dir = local_client.localCacheDir()
    alternate_kbucket_cache_dirs = local_client.alternateLocalCacheDirs()

    env_vars = []

    singularity_opts.append('-B {}:{}'.format(kbucket_cache_dir, '/sha1-cache'))
    env_vars.append('KBUCKET_CACHE_DIR=/sha1-cache')
    alt_dirs_in_container = []
    for ii, alt_cache_dir in enumerate(alternate_kbucket_cache_dirs):
        dir_in_container = '/sha1-cache-alt-{}'.format(ii)
        singularity_opts.append('-B {}:{}'.format(alt_cache_dir, dir_in_container))
        alt_dirs_in_container.append(dir_in_container)
    env_vars.append('KBUCKET_CACHE_DIR_ALT={}'.format(':'.join(alt_dirs_in_container)))
    singularity_opts.append('-B /tmp:/tmp')
    singularity_opts.append('--contain')
    singularity_opts.append('-e')
    return singularity_opts, env_vars

def _read_text_file(fname):
    with open(fname) as f:
        return f.read()


def _write_text_file(fname, str):
    with open(fname, 'w') as f:
        f.write(str)

def _get_file_ext(fname):
    _, ext = os.path.splitext(fname)
    return ext

def _make_remote_url_for_file(fname):
    if fname.startswith('sha1://'):
        return fname
    elif fname.startswith('kbucket://') or fname.startswith('sha1dir://'):
        return fname
    else:
        sha1 = local_client.computeFileSha1(fname)
        return 'sha1://'+sha1+'/'+os.path.basename(fname)

# def _run_command_and_print_output(command, timeout=None):
#     timer = time.time()
#     with subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stderr=subprocess.PIPE) as process:
#         while True:
#             elapsed = time.time() - timer
#             if timeout is not None:
#                 if elapsed > timeout:
#                     print('ELAPSED TIME EXCEEEDS TIMEOUT -- KILLING PROCESS -- {} > {} sec'.format(elapsed, timeout))
#                     process.terminate()
#                     return -1
#             output_stdout= process.stdout.readline()
#             output_stderr = process.stderr.readline()
#             if (not output_stdout) and (not output_stderr) and (process.poll() is not None):
#                 break
#             if output_stdout:
#                 print(output_stdout.decode())
#             if output_stderr:
#                 print(output_stderr.decode())
#         rc = process.poll()
#         return rc

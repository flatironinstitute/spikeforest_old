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

class MountainJob():
    def __init__(self):
        self.result=None
        self._processor=None
        self._job=None

    def isNull(self):
        return (self._job is None)

    def getObject(self):
        return deepcopy(self._job)

    def initFromObject(self, job_object):
        self._processor=None
        self._job=deepcopy(job_object)

    def addFilesToRealize(self, files_to_realize):
        if self._job is None:
            return
        if type(files_to_realize)==str:
            self._job['additional_files_to_realize'].append(files_to_realize)
        elif type(files_to_realize)==list:
            self._job['additional_files_to_realize'].extend(files_to_realize)
        else:
            raise Exception('Unexpected type of files_to_realize in addFilesToRealize')

    def getFilesToRealize(self):
        if self._job is None:
            return []
        # These are the files needed at the compute location to actually run the job
        ret=[]
        if self._job['container']:
            ret.append(self._job['container'])
        for input0 in self._job['inputs'].values():
            if not input0.get('directory', False):
                ret.append(input0['path'])
        if self._job['processor_code']:
            ret.append(self._job['processor_code'])
        if 'additional_files_to_realize' in self._job:
            ret.extend(self._job['additional_files_to_realize'])
        return ret

    def useRemoteUrlsForInputFiles(self):
        if self._job is None:
            return
        if self._job['container']:
            self._job['container'] = _make_remote_url_for_file(self._job['container'])
        for input_name, input0 in self._job['inputs'].items():
            if not input0.get('directory', False):
                self._job['inputs'][input_name]['path'] = _make_remote_url_for_file(input0['path'])
        if 'additional_files_to_realize' in self._job:
            for ii, fname in enumerate(self._job['additional_files_to_realize']):
                self._job['additional_files_to_realize'][ii] = _make_remote_url_for_file(fname)

    def initFromProcessor(self, proc, _label=None, _force_run=None, _keep_temp_files=None, _container=None, _use_cache=True, _timeout=None, **kwargs):
        timer=time.time()
        if _force_run is None:
            _force_run = (os.environ.get('MLPROCESSORS_FORCE_RUN', '') == 'TRUE')

        if _keep_temp_files is None:
            _keep_temp_files = (os.environ.get('MLPROCESSORS_KEEP_TEMP_FILES', '') == 'TRUE')

        if _container == 'default':
            if hasattr(proc, 'CONTAINER'):
                _container = proc.CONTAINER
        if _container:
            if not _file_exists_or_is_sha1_url(_container):
                raise Exception('Unable to find container file: '+_container)
        
        if _label is None:
            _label='{} (version: {})'.format(proc.NAME, proc.VERSION)

        inputs = dict()
        for input0 in proc.INPUTS:
            name0 = input0.name
            if name0 in kwargs:
                fname0 = kwargs[name0]
                if input0.directory:
                    if not _directory_exists(fname0):
                        raise Exception('Unable to find input directory {}: {}'.format(name0, fname0))
                    inputs[name0] = dict(
                        directory = True,
                        path = fname0
                    )
                else:
                    if not _file_exists_or_is_sha1_url(fname0):
                        raise Exception('Unable to find input file {}: {}'.format(name0, fname0))
                    inputs[name0] = dict(
                        path = fname0
                    )
                
            else:
                if not input0.optional:
                    raise Exception('Missing required input: {}'.format(name0))

        outputs = dict()
        for output0 in proc.OUTPUTS:
            name0 = output0.name
            if name0 in kwargs:
                val0 = kwargs[name0]
                if type(val0) == str:
                    _, file_extension = os.path.splitext(val0)
                    outputs[name0] = dict(
                        ext = file_extension,
                        dest_path = os.path.abspath(val0)
                    )
                elif type(val0) == dict:
                    outputs[name0] = val0
                else:
                    raise Exception('Type of output {} cannot be {}'.format(name0, str(type(val0))))
            else:
                if not output0.optional:
                    raise Exception('Missing required output: {}'.format(name0))

        parameters = dict()
        for param0 in proc.PARAMETERS:
            name0 = param0.name
            if name0 not in kwargs:
                if param0.optional:
                    val0 = param0.default
                else:
                    raise Exception('Missing required parameter: {}'.format(name0))
            else:
                val0 = kwargs[name0]
            parameters[name0] = val0

        output_signatures = dict()

        for output_name in list(outputs.keys())+['--runtime-info--','--console-out--']:
            output_signatures[output_name] = _compute_mountain_job_output_signature(
                processor_name=proc.NAME,
                processor_version=proc.VERSION,
                inputs=inputs,
                parameters=parameters,
                output_name=output_name
            )

        try:
            processor_source_fname = os.path.abspath(inspect.getsourcefile(proc))
        except:
            print(proc)
            print('Warning: Unable to get source file for processor {}. You will not be able to run this on a compute resource.'.format(proc.NAME))
            processor_source_fname = None
        if processor_source_fname is not None:
            processor_source_dirname = os.path.dirname(processor_source_fname)
            processor_source_basename = os.path.basename(processor_source_fname)
            processor_source_basename_noext = os.path.splitext(processor_source_basename)[0]
            code = _read_python_code_of_directory(
                processor_source_dirname,
                additional_files=getattr(proc, 'ADDITIONAL_FILES', []),
                exclude_init=True
            )
            code['files'].append(dict(
                name='__init__.py',
                content='from .{} import {}'.format(
                    processor_source_basename_noext, proc.__name__)
            ))
            code = mt.saveObject(object = code)
        else:
            code = None

        if hasattr(proc, 'ENVIRONMENT_VARIABLES'):
            environment_variables = proc.ENVIRONMENT_VARIABLES
        else:
            environment_variables = []

        self._processor=proc
        self._job=dict(
            processor_name=proc.NAME,
            processor_version=proc.VERSION,
            processor_class_name=proc.__name__,
            processor_code=code,
            label=_label,
            inputs=inputs,
            outputs=outputs,
            parameters=parameters,
            output_signatures=output_signatures,
            container=_container,
            force_run=_force_run,
            use_cache=_use_cache,
            keep_temp_files=_keep_temp_files,
            environment_variables=environment_variables,
            additional_files_to_realize=[],
            timeout=_timeout
        )

    def execute(self):
        if self._job is None:
            return MountainJobResult()
        container=self._job['container']
        force_run=self._job['force_run']
        use_cache=self._job['use_cache']
        keep_temp_files=self._job['keep_temp_files']
        job_timeout=self._job.get('timeout', None)

        if (use_cache) and (not force_run):
            result = self._find_result_in_cache()
            if result:
                self._copy_outputs_from_result_to_dest_paths(result)
                return result

        keep_temp_files=True
        with TemporaryDirectory(remove=(not keep_temp_files), prefix='tmp_execute_outputdir_'+self._job['processor_name']) as tmp_output_path:
            attributes_for_processor = dict()
            tmp_output_file_names = dict()
            output_files_to_copy = []
            output_files = dict()
            inputs_to_bind = []
            tmp_process_console_out_fname = os.path.join(tmp_output_path, 'process_console_out.txt')
            tmp_process_console_out_fname_in_container = os.path.join('/processor_outputs', 'process_console_out.txt')
            for input_name, input0 in self._job['inputs'].items():
                if not input0.get('directory', False):
                    input_fname = self._realize_input(input0['path'])
                    if not input_fname:
                        raise Exception('Unable to realize input {}: {}'.format(input_name, input0['path']))
                else:
                    input_fname = input0['path']
                if not container:
                    attributes_for_processor[input_name] = input_fname
                else:
                    ext = _get_file_ext(input_fname) or '.in'
                    
                    if input0.get('directory', False) and (input0['path'].startswith('kbucket://')):
                        infile_in_container = input0['path']
                    else:
                        infile_in_container = '/processor_inputs/{}{}'.format(input_name, ext)
                        inputs_to_bind.append((input_fname, infile_in_container))
                    attributes_for_processor[input_name] = infile_in_container
            for output_name, output_value in self._job['outputs'].items():
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
            for param_name, param_value in self._job['parameters'].items():
                attributes_for_processor[param_name] = param_value

            runtime_capture = ConsoleCapture()
            runtime_capture.start_capturing()
            R = MountainJobResult()
            if (not container) and self._processor:
                # This means we can just run it directly
                X = self._processor()  # instance
                for attr_name, attr_val in attributes_for_processor.items():
                    setattr(X, attr_name, attr_val)
                try:
                    X.run()
                    retcode = 0
                except:
                    traceback.print_exc()
                    runtime_capture.stop_capturing()
                    R.retcode = -1
                    R.runtime_info = runtime_capture.runtimeInfo()
                    R.console_out = mt.saveText(text = runtime_capture.consoleOut(), basename='console_out.txt')
                    return R
            else:
                # Otherwise we need to do code generation
                timer = time.time()
                with TemporaryDirectory(remove=(not keep_temp_files), prefix='tmp_execute_'+self._job['processor_name']) as temp_path:
                    self._generate_execute_code(temp_path, attributes_for_processor=attributes_for_processor)
                    if not container:
                        env = os.environ # is this needed?
                        python_cmd='python3 {}/run.py &>{}'.format(temp_path, tmp_process_console_out_fname)
                        if job_timeout:
                            # python_cmd = 'timeout -s INT {}s {}'.format(job_timeout, python_cmd)
                            python_cmd = 'timeout {}s {}'.format(job_timeout, python_cmd)
                        print('Running: '+python_cmd)
                        #retcode = subprocess.call(python_cmd, shell=True, env=env)
                        retcode = os.system('bash -c "{}"'.format(python_cmd.replace('"','\\"')))
                    else:
                        print('Realizing container file: {}'.format(container))
                        container_orig = container
                        container = mt.realizeFile(container)
                        if not container:
                            raise Exception('Unable to realize container file: {}'.format(container_orig))
                        singularity_opts = _get_singularity_opts()
                        singularity_opts.append('-B {}:{}'.format(temp_path, '/run_in_container'))
                        singularity_opts.append('-B {}:{}'.format(tmp_output_path, '/processor_outputs'))
                        for tobind in inputs_to_bind:
                            singularity_opts.append('-B {}:{}'.format(tobind[0], tobind[1]))
                        env_vars = []
                        environment_variables = self._job.get('environment_variables', [])
                        for v in environment_variables:
                            val = os.environ.get(v, '')
                            if val:
                                env_vars.append('{}={}'.format(v, val))
                        python_cmd = 'python3 /run_in_container/run.py  &>{}'.format(tmp_process_console_out_fname_in_container)
                        if job_timeout:
                            # python_cmd = 'timeout -s INT {}s {}'.format(job_timeout, python_cmd)
                            python_cmd = 'timeout {}s {}'.format(job_timeout, python_cmd)
                        singularity_cmd = 'singularity exec {} {} bash -c "KBUCKET_CACHE_DIR=/sha1-cache {} {}"'.format(
                            ' '.join(singularity_opts), container, ' '.join(env_vars), python_cmd)
                        
                        env = os.environ # is this needed?
                        print('Running: '+singularity_cmd)
                        #retcode = subprocess.call(singularity_cmd, shell=True, env=env)
                        retcode = os.system('bash -c "{}"'.format(singularity_cmd.replace('"','\\"')))
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
                if job_timeout:
                    if retcode == 124:
                        print('RETURN CODE IS 124 indicating the process exceeded the timeout threshold of {}s'.format(job_timeout))
                elapsed = time.time() - timer
                print('========== {} exited with code {} after {} sec'.format(self._job['processor_name'], retcode, elapsed))
                print('================================================================================')
            
            runtime_capture.stop_capturing()
            R.retcode=retcode
            R.runtime_info = runtime_capture.runtimeInfo()
            R.console_out = mt.saveText(text = runtime_capture.consoleOut(), basename='console_out.txt')
            R.outputs=dict()
            if retcode == 0:
                for output_tocopy in output_files_to_copy:
                    print('Saving output: {} -> {}'.format(output_tocopy[0], output_tocopy[1]))
                    shutil.copyfile(output_tocopy[0], output_tocopy[1])
                for output_name, fname in output_files.items():
                    if not os.path.exists(fname):
                        raise Exception('Unexpected: output file {} does not exist: {}'.format(output_name, fname), os.path.exists(fname))
                    R.outputs[output_name] = mt.saveFile(path=fname)

            if (retcode == 0) and use_cache:
                self._store_result_in_cache(R)

            return R

    def _realize_input(self, fname):
        if fname.startswith('kbucket://'):
            if mt.findFile(fname):
                return mt.realizeFile(fname)
            else:
                # must be a directory
                return fname
        else:
            return mt.realizeFile(fname)

    def _generate_execute_code(self, temp_path, attributes_for_processor):
        code = mt.loadObject(path = self._job['processor_code'])
        if code is None:
            raise Exception('Unable to load processor code for job.')
        _write_python_code_to_directory(temp_path+'/processor_source', code)
        
        processor_class_name = self._job['processor_class_name']

        # Code generation
        code = """
from processor_source import {processor_class_name}
import sys

def main():
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
        """
        
        set_attributes_code = []
        for attr_name, attr_val in attributes_for_processor.items():
            set_attributes_code.append(
                "    setattr(X, '{}', {})".format(attr_name, _code_generate_value(attr_val))
            )
        set_attributes_code = '\n'.join(set_attributes_code)
        code = code.replace('{processor_class_name}', processor_class_name)
        code = code.replace('{set_attributes}', set_attributes_code)

        _write_text_file(os.path.join(temp_path,'run.py'), code)

    def _find_result_in_cache(self):
        output_signatures = self._job['output_signatures']
        output_paths=dict()
        for output_name, signature in output_signatures.items():
            output_path = mt.getValue(key=signature)
            if not output_path:
                return None
            output_paths[output_name] = output_path

        runtime_info=mt.loadObject(path=output_paths['--runtime-info--'])
        if not runtime_info:
            return None
        
        R = MountainJobResult()
        R.retcode=0
        R.runtime_info=runtime_info
        R.console_out = output_paths['--console-out--']
        R.outputs=dict()
        for output_name in self._job['outputs'].keys():
            R.outputs[output_name] = output_paths[output_name]
        return R

    def _store_result_in_cache(self, result):
        output_signatures = self._job['output_signatures']
        for output_name in self._job['outputs'].keys():
            if output_name in result.outputs:
                mt.setValue(key=output_signatures[output_name], value=result.outputs[output_name])
        runtime_info_path = mt.saveObject(object=result.runtime_info, basename='runtime_info.json')
        mt.setValue(key=output_signatures['--runtime-info--'], value=runtime_info_path)
        mt.setValue(key=output_signatures['--console-out--'], value=result.console_out)

    def _copy_outputs_from_result_to_dest_paths(self, result):
        for output_name, output0 in self._job['outputs'].items():
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
                mt.realizeFile(result.outputs[output_name], dest_path=dest_path)
                result.outputs[output_name] = dest_path

class MountainJobResult():
    def __init__(self):
        self.retcode=0
        self.console_out=None
        self.runtime_info=None
        self.outputs=None

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

def _compute_mountain_job_output_signature(*, processor_name, processor_version, inputs, parameters, output_name):
    input_hashes=dict()
    for input_name, input0 in inputs.items():
        if input0.get('directory', False):
            input_hashes[input_name] = mt.computeDirHash(input0['path'])
        else:
            input_hashes[input_name] = mt.computeFileSha1(input0['path'])

    signature_obj = dict(
        processor_name=processor_name,
        processor_version=processor_version,
        inputs=input_hashes,
        parameters=parameters,
        output_name=output_name
    )
    signature_string = json.dumps(signature_obj, sort_keys=True)
    return _sha1(signature_string)
        
def _sha1(str):
    hash_object = hashlib.sha1(str.encode('utf-8'))
    return hash_object.hexdigest()

def _file_exists_or_is_sha1_url(fname):
    if fname.startswith('sha1://'):
        return True
    if mt.findFile(path=fname):
        return True
    return False

def _directory_exists(fname):
    if fname.startswith('kbucket://'):
        a = mt.readDir(path=fname,include_sha1=False)
        return (a is not None)
    return os.path.isdir(fname)

class TemporaryDirectory():
    def __init__(self, remove=True, prefix='tmp'):
        self._remove = remove
        self._prefix = prefix
    def __enter__(self):
        kbucket_cache_dir = os.environ.get('KBUCKET_CACHE_DIR', None)
        if kbucket_cache_dir:
            dirpath = os.path.join(kbucket_cache_dir, 'tmp')
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
        else:
            dirpath = None
        self._path = tempfile.mkdtemp(prefix = self._prefix, dir=dirpath)
        return self._path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._remove:
            shutil.rmtree(self._path)

    def path(self):
        return self._path

def _read_python_code_of_directory(dirname, additional_files=[], exclude_init=True):
    patterns = ['*.py']+additional_files
    files = []
    dirs = []
    for fname in os.listdir(dirname):
        if os.path.isfile(dirname+'/'+fname):
            matches = False
            for pattern in patterns:
                if fnmatch.fnmatch(fname, pattern):
                    matches = True
            if exclude_init and (fname == '__init__.py'):
                matches = False
            if matches:
                with open(dirname+'/'+fname) as f:
                    txt = f.read()
                files.append(dict(
                    name=fname,
                    content=txt
                ))
        elif os.path.isdir(dirname+'/'+fname):
            if (not fname.startswith('__')) and (not fname.startswith('.')):
                content = _read_python_code_of_directory(
                    dirname+'/'+fname, additional_files=additional_files, exclude_init=False)
                if len(content['files'])+len(content['dirs']) > 0:
                    dirs.append(dict(
                        name=fname,
                        content=content
                    ))
    return dict(
        files=files,
        dirs=dirs
    )

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

def _get_singularity_opts():
    singularity_opts = []
    kbucket_cache_dir = mt.localCacheDir()
    singularity_opts.append('-B {}:{}'.format(kbucket_cache_dir, '/sha1-cache'))
    singularity_opts.append('-B /tmp:/tmp')
    singularity_opts.append('--contain')
    singularity_opts.append('-e')
    return singularity_opts

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
    elif fname.startswith('kbucket://'):
        return fname
    else:
        sha1 = mt.computeFileSha1(fname)
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

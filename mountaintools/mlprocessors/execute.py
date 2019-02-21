import types
import types
import hashlib
import json
import os
import shutil
import tempfile
import subprocess
from cairio import client as ca
import inspect
from subprocess import Popen, PIPE
import shlex
import time
import sys
import multiprocessing
import random
import fnmatch


def sha1(str):
    hash_object = hashlib.sha1(str.encode('utf-8'))
    return hash_object.hexdigest()


def compute_job_input_signature(val, input_name, *, directory):
    if type(val) == str:
        if val.startswith('sha1://'):
            if directory:
                raise Exception('sha1:// path not allowed for directory input')
            list = str.split(val, '/')
            return list[2]
        elif val.startswith('kbucket://'):
            if directory:
                hash0 = ca.computeDirHash(val)
                if not hash0:
                    raise Exception(
                        'Unable to compute directory hash for input: {}'.format(input_name))
                return hash0
            else:
                sha1 = ca.computeFileSha1(val)
                if not sha1:
                    raise Exception(
                        'Unable to compute file sha-1 for input: {}'.format(input_name))
                return sha1
        else:
            if os.path.exists(val):
                if directory:
                    if os.path.isdir(val):
                        hash0 = ca.computeDirHash(val)
                        if not hash0:
                            raise Exception(
                                'Unable to compute hash for directory input: {} ({})'.format(input_name, val))
                        return hash0
                    else:
                        raise Exception(
                            'Input is not a directory: {}'.format(input_name))
                else:
                    if os.path.isfile(val):
                        sha1 = ca.computeFileSha1(val)
                        if not sha1:
                            raise Exception(
                                'Unable to compute sha-1 of input: {} ({})'.format(input_name, val))
                        return sha1
                    else:
                        raise Exception(
                            'Input is not a file: {}'.format(input_name))
            else:
                raise Exception('Input file does not exist: '+val)
    else:
        if hasattr(val, 'signature'):
            return getattr(val, 'signature')
        else:
            raise Exception(
                "Unable to compute signature for input: {}".format(input_name))


def get_file_extension(fname):
    if type(fname) == str:
        name, ext = os.path.splitext(fname)
        return ext
    else:
        return ''


def compute_processor_job_stats_signature(self):
    return compute_processor_job_output_signature(self, '--stats--')


def compute_processor_job_console_out_signature(self):
    return compute_processor_job_output_signature(self, '--console-out--')


def compute_processor_job_output_signature(self, output_name):
    processor_inputs = []
    job_inputs = []
    for input0 in self.INPUTS:
        name0 = input0.name
        val0 = getattr(self, name0)
        processor_inputs.append(dict(
            name=name0
        ))
        job_inputs.append(dict(
            name=name0,
            signature=compute_job_input_signature(
                val0, input_name=name0, directory=input0.directory),
            ext=get_file_extension(val0)
        ))
    processor_outputs = []
    job_outputs = []
    for output0 in self.OUTPUTS:
        name0 = output0.name
        processor_outputs.append(dict(
            name=name0
        ))
        val0 = getattr(self, name0)
        if type(val0) == str:
            job_outputs.append(dict(
                name=name0,
                ext=get_file_extension(val0)
            ))
        else:
            job_outputs.append(dict(
                name=name0,
                ext=val0['ext']
            ))
    processor_parameters = []
    job_parameters = []
    for param0 in self.PARAMETERS:
        name0 = param0.name
        processor_parameters.append(dict(
            name=name0
        ))
        job_parameters.append(dict(
            name=name0,
            value=getattr(self, name0)
        ))
    processor_obj = dict(
        processor_name=self.NAME,
        processor_version=self.VERSION,
        inputs=processor_inputs,
        outputs=processor_outputs,
        parameters=processor_parameters
    )
    signature_obj = dict(
        processor=processor_obj,
        inputs=job_inputs,
        outputs=job_outputs,
        parameters=job_parameters
    )
    if output_name:
        signature_obj["output_name"] = output_name
    signature_string = json.dumps(signature_obj, sort_keys=True)
    return sha1(signature_string)


def create_temporary_file(fname):
    tempdir = os.environ.get('KBUCKET_CACHE_DIR', tempfile.gettempdir())
    tmp = tempdir+'/mlprocessors'
    if not os.path.exists(tmp):
        os.mkdir(tmp)
    return tmp+'/'+fname


class ProcessorExecuteOutput():
    def __init__(self):
        self.outputs = dict()
        self.stats = dict()
        self.console_out = ''


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


def _read_text_file(fname):
    with open(fname) as f:
        return f.read()


def _write_text_file(fname, str):
    with open(fname, 'w') as f:
        f.write(str)


def _read_text_file(fname):
    with open(fname) as f:
        return f.read()


def _write_text_file(fname, str):
    with open(fname, 'w') as f:
        f.write(str)


def _get_expanded_args(args):
    expanded_args_list = []
    for key in args:
        val = args[key]
        if type(val) == str:
            val = "'{}'".format(val)
        elif type(val) == dict:
            val = "{}".format(json.dumps(val))
        expanded_args_list.append('{}={}'.format(key, val))
    expanded_args = ', '.join(expanded_args_list)
    return expanded_args


def _execute_in_container(proc, X, *, container, tempdir, _system_call_prefix, **kwargs):
    # Note: if container is '', then we are just executing on the host machine
    singularity_opts = []
    if container:
        kbucket_cache_dir = ca.localCacheDir()
        singularity_opts.append(
            '-B {}:{}'.format(kbucket_cache_dir, '/sha1-cache'))
        singularity_opts.append('-B /tmp:/tmp')

    for input0 in proc.INPUTS:
        name0 = input0.name
        fname0 = getattr(X, name0)
        if fname0:
            if fname0.startswith('kbucket://') or fname0.startswith('sha1://'):
                pass
            else:
                fname0 = os.path.abspath(fname0)
                if container:
                    fname2 = '/execute_in_container/input_{}'.format(name0)
                    singularity_opts.append('-B {}:{}'.format(fname0, fname2))
                else:
                    fname2 = fname0
                kwargs[name0] = fname2

    for output0 in proc.OUTPUTS:
        name0 = output0.name
        val = getattr(X, name0)
        if val:
            val = os.path.abspath(val)
            dirname = os.path.dirname(val)
            filename = os.path.basename(val)
            dirname2 = '/execute_in_container/outputdir_{}'.format(name0)
            if container:
                kwargs[name0] = dirname2+'/'+filename
                singularity_opts.append('-B {}:{}'.format(dirname, dirname2))
            else:
                kwargs[name0] = val

    expanded_kwargs = _get_expanded_args(kwargs)

    processor_source_fname = inspect.getsourcefile(proc)
    processor_source_dirname = os.path.dirname(processor_source_fname)

    # Note: in future, we do not want to mount mountaintools! This was a temp hack because I did not have wi-fi access
    mountaintools_source_dirname = os.path.abspath(
        os.path.dirname(os.path.realpath(__file__))+'/..')

    if not processor_source_fname:
        raise Exception(
            'inspect.getsourcefile() returned empty for processor.')
    if container:
        singularity_opts.append(
            '-B {}:/execute_in_container/processor_source'.format(processor_source_dirname))
        # Note: in future, we do not want to mount mountaintools! This was a temp hack because I did not have wi-fi access
        singularity_opts.append(
            '-B {}:/execute_in_container/mountaintools'.format(mountaintools_source_dirname))
    else:
        os.symlink(processor_source_dirname, tempdir+'/processor_source')
        # Note: in future, we do not want to mount mountaintools! This was a temp hack because I did not have wi-fi access
        os.symlink(mountaintools_source_dirname, tempdir+'/mountaintools')

    # Code generation
    code = """
from processor_source import {processor_class_name}

def main():
    {processor_class_name}.execute({expanded_kwargs})

if __name__ == "__main__":
    main()
    """
    code = code.replace('{processor_class_name}', proc.__name__)
    code = code.replace('{expanded_kwargs}', expanded_kwargs)

    _write_text_file(tempdir+'/execute_in_container.py', code)
    if container:
        singularity_opts.append(
            '-B {}:/execute_in_container/execute_in_container.py'.format(tempdir+'/execute_in_container.py'))

    env_vars = []
    if hasattr(proc, 'ENVIRONMENT_VARIABLES'):
        list = proc.ENVIRONMENT_VARIABLES
        for v in list:
            val = os.environ.get(v, '')
            if val:
                env_vars.append('{}={}'.format(v, val))
    if container:
        singularity_opts.append('--contain')
        singularity_opts.append('-e')
        # Note: in future, we do not want to mount mountaintools! This was a temp hack because I did not have wi-fi access
        singularity_cmd = 'singularity exec {} {} bash -c "PYTHONPATH=/execute_in_container/mountaintools KBUCKET_CACHE_DIR=/sha1-cache {} python3 /execute_in_container/execute_in_container.py"'.format(
            ' '.join(singularity_opts), container, ' '.join(env_vars))
    else:
        singularity_cmd = 'python3 {}/execute_in_container.py'.format(tempdir)
        if _system_call_prefix is not None:
            singularity_cmd = '{} {}'.format(
                _system_call_prefix, singularity_cmd)
        # singularity_cmd='bash -c "{}"'.format(singularity_cmd)

    retcode, console_out = _run_command_and_print_output(singularity_cmd)
    if retcode != 0:
        raise Exception('Processor returned a non-zero exit code')

    return console_out


def _shell_execute(cmd):
    popen = subprocess.Popen('{}'.format(cmd), stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
    console_output_lines = []
    for stdout_line in iter(popen.stdout.readline, ""):
        # yield stdout_line
        console_output_lines.append(stdout_line)
        print(stdout_line, end='\r')
    popen.stdout.close()
    return_code = popen.wait()
    return return_code, ''.join(console_output_lines)


def _run_command_and_print_output(cmd):
    print('RUNNING: '+cmd)
    return _shell_execute(cmd)


def _run_command_and_print_output_old(command):
    print('RUNNING: '+command)
    with Popen(shlex.split(command), stdout=PIPE, stderr=PIPE) as process:
        while True:
            output_stdout = process.stdout.readline()
            output_stderr = process.stderr.readline()
            if (not output_stdout) and (not output_stderr) and (process.poll() is not None):
                break
            if output_stdout:
                print(output_stdout.decode())
            if output_stderr:
                print(output_stderr.decode())
        rc = process.poll()
        return rc


def createJob(proc, _container=None, _cache=True, _force_run=None, _keep_temp_files=None, **kwargs):
    if _force_run is None:
        if os.environ.get('MLPROCESSORS_FORCE_RUN', '') == 'TRUE':
            _force_run = True
        else:
            _force_run = False

    if _keep_temp_files is None:
        if os.environ.get('MLPROCESSORS_KEEP_TEMP_FILES', '') == 'TRUE':
            _keep_temp_files = True
        else:
            _keep_temp_files = False

    if _container == 'default':
        if hasattr(proc, 'CONTAINER'):
            _container = proc.CONTAINER

    inputs = dict()
    for input0 in proc.INPUTS:
        name0 = input0.name
        if name0 not in kwargs:
            raise Exception('Missing input: {}'.format(name0))
        fname0 = kwargs[name0]
        if fname0.startswith('kbucket://') or fname0.startswith('sha1://'):
            pass
        else:
            fname0 = os.path.abspath(fname0)
            if not os.path.exists(fname0):
                raise Exception(
                    'Input {} does not exist: {}'.format(name0, fname0))
            if os.path.isfile(fname0):
                sha1_url = ca.saveFile(fname0)
                if not sha1_url:
                    raise Exception(
                        'Problem saving input {} to kbucket ({})'.format(name0, fname0))
                fname0 = sha1_url
            else:
                pass  # TODO: think about how to handle directories -- probably just give a warning message
        inputs[name0] = fname0

    outputs = dict()
    for output0 in proc.OUTPUTS:
        name0 = output0.name
        if name0 not in kwargs:
            raise Exception('Missing output: {}'.format(name0))
        val0 = kwargs[name0]
        if type(val0) != dict:
            raise Exception('Type of output {} cannot be {}'.format(
                name0, str(type(val0))))
        outputs[name0] = val0
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
    if _container:
        if _container.startswith('kbucket://') or _container.startswith('sha1://'):
            pass
        else:
            newpath = ca.saveFile(_container)
            if not newpath:
                raise Exception('Unable to save (or upload) container file.')
            if not _container.startswith('sha1://'):
                _container = newpath
    processor_source_fname = inspect.getsourcefile(proc)
    processor_source_dirname = os.path.dirname(processor_source_fname)
    processor_source_basename = os.path.basename(processor_source_fname)
    processor_source_basename_noext = os.path.splitext(
        processor_source_basename)[0]
    code = _read_python_code_of_directory(
        processor_source_dirname, additional_files=getattr(proc, 'ADDITIONAL_FILES', []), exclude_init=True)
    code['files'].append(dict(
        name='__init__.py',
        content='from .{} import {}'.format(
            processor_source_basename_noext, proc.__name__)
    ))
    processor_job = dict(
        command='execute_mlprocessor',
        label='{} (version: {}) (container: {})'.format(
            proc.NAME, proc.VERSION, _container),
        processor_name=proc.NAME,
        processor_version=proc.VERSION,
        processor_class_name=proc.__name__,
        processor_code=ca.saveObject(code, basename='code.json'),
        container=_container,
        inputs=inputs,
        outputs=outputs,
        parameters=parameters
    )
    if _force_run:
        processor_job['_force_run'] = True
    if _cache:
        processor_job['_cache'] = True
    if _keep_temp_files:
        processor_job['_keep_temp_files'] = True
    return processor_job


_realized_containers = set()


def _prepare_processor_job(job):
    container = job.get('container', None)
    if container:
        if container not in _realized_containers:
            print('realizing container: '+container)
            a = ca.realizeFile(path=container)
            if a:
                _realized_containers.add(container)
            else:
                raise Exception('Unable to realize container file: '+container)
    files_to_realize = job.get('files_to_realize', [])
    for fname in files_to_realize:
        print('realizing file: '+fname)
        a = ca.realizeFile(path=fname)
        if not a:
            raise Exception('Unable to realize file: '+fname)


def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))


def executeBatch(*, jobs, label='', num_workers=None, compute_resource=None, batch_name=None):

    print('executeBatch')
    # make sure the files to realize are absolute paths
    for job in jobs:
        if 'files_to_realize' in job:
            for i, fname in enumerate(job['files_to_realize']):
                if fname.startswith('kbucket://') or fname.startswith('sha1://'):
                    pass
                else:
                    fname = os.path.abspath(fname)
                job['files_to_realize'][i] = fname

    if num_workers is not None:
        if compute_resource is not None:
            raise Exception('Cannot specify num_workers and compute_resource.')
        pool = multiprocessing.Pool(num_workers)
        results = pool.map(executeJob, jobs)
        pool.close()
        pool.join()
        for i, job in enumerate(jobs):
            job['result'] = results[i]
        return

    if compute_resource is not None:
        import batcho
        if batch_name is None:
            batch_name = 'batch_'+_random_string(10)
        batcho.set_batch(batch_name=batch_name, label=label, jobs=jobs,
                         compute_resource=compute_resource)
        last_update_string = ''
        while True:
            batch_status = batcho.get_batch_status(batch_name=batch_name)
            if batch_status is None:
                update_string = 'Waiting...'
            else:
                batch_status0 = batch_status.get('status', '')
                if batch_status0 == 'finished':
                    print('Finished.')
                    break
                if batch_status0 == 'error':
                    err0 = batch_status.get('error', '')
                    raise Exception('Error executing batch: {}'.format(err0))
                statuses_list = list(batcho.get_batch_job_statuses(
                    batch_name=batch_name).values())
                num_ready = statuses_list.count('ready')
                num_running = statuses_list.count('running')
                num_finished = statuses_list.count('finished')
                update_string = '({})\n{} --- {}: {} ready, {} running, {} finished, {} total jobs'.format(
                    batch_name, label, batch_status0, num_ready, num_running, num_finished, len(jobs))
            if update_string != last_update_string:
                print(update_string)
            last_update_string = update_string
            time.sleep(1)

        results0 = batcho.get_batch_results(batch_name=batch_name)
        if results0 is None:
            raise Exception('Unable to get batch results.')
        for i, job in enumerate(jobs):
            job['result'] = results0['results'][i]['result']
        return

    timer = time.time()
    for job in jobs:
        job['result'] = executeJob(job)


def executeJob(job):
    timer = time.time()
    tempdir = tempfile.mkdtemp()
    try:
        processor_code = ca.loadObject(path=job['processor_code'])
        _write_python_code_to_directory(
            tempdir+'/processor_source', processor_code)

        processor_class_name = job['processor_class_name']

        container = job.get('container', None)
        if container:
            container = ca.realizeFile(path=container)

        execute_kwargs = dict(
            _cache=job.get('_cache', None),
            _force_run=job.get('_force_run', None),
            _keep_temp_files=job.get('_keep_temp_files', None),
            _container=container,
        )
        for key in job['inputs']:
            execute_kwargs[key] = job['inputs'][key]
        temporary_output_files = dict()
        for key in job['outputs']:
            out0 = job['outputs'][key]
            tmp_fname = tempdir+'/output_'+key+out0['ext']
            temporary_output_files[key] = tmp_fname
            execute_kwargs[key] = tmp_fname
        for key in job['parameters']:
            execute_kwargs[key] = job['parameters'][key]
        expanded_execute_kwargs = _get_expanded_args(execute_kwargs)

        # Code generation
        code = """
from processor_source import {processor_class_name}

def main():
    {processor_class_name}.execute({expanded_execute_kwargs})

if __name__ == "__main__":
    main()
        """
        code = code.replace('{processor_class_name}', processor_class_name)
        code = code.replace('{expanded_execute_kwargs}',
                            expanded_execute_kwargs)

        _write_text_file(tempdir+'/execute.py', code)

        retcode, console_out = _run_command_and_print_output(
            'python3 {}/execute.py'.format(tempdir))
        if retcode != 0:
            raise Exception('Non-zero return code when running processor job')
        ret = dict(
            outputs=dict(),
            console_out=console_out
        )
        for key in job['outputs']:
            out0 = job['outputs'][key]
            if out0.get('upload', False):
                ret['outputs'][key] = ca.saveFile(
                    temporary_output_files[key], basename=key+out0['ext'], confirm=True)
            else:
                ret['outputs'][key] = 'sha1://' + \
                    ca.computeFileSha1(
                        temporary_output_files[key])+'/'+key+out0['ext']
        return ret
    except:
        shutil.rmtree(tempdir)
        raise
    shutil.rmtree(tempdir)
    return ret


try:
    import batcho
    batcho_ok = True
except:
    print('Warning: unable to import batcho.')
    batcho_ok = False
if batcho_ok:
    def _batcho_execute_mlprocessor_prepare(job):
        _prepare_processor_job(job)

    def _batcho_execute_mlprocessor_run(job):
        return executeJob(job)
    batcho.register_job_command(command='execute_mlprocessor',
                                prepare=_batcho_execute_mlprocessor_prepare, run=_batcho_execute_mlprocessor_run)


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
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def start_capturing(self):
        self._tmp_fname = tempfile.mktemp(suffix='.txt')
        self._file_handle = open(self._tmp_fname, 'w')
        sys.stdout = Logger2(self._file_handle, self._original_stdout)
        sys.stderr = Logger2(self._file_handle, self._original_stderr)

    def stop_capturing(self):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self._file_handle.close()
        with open(self._tmp_fname, 'r') as f:
            self._console_out = f.read()

    def consoleOut(self):
        return self._console_out


def execute(proc, _cache=True, _force_run=None, _container=None, _system_call=False, _system_call_prefix=None, _keep_temp_files=None, **kwargs):

    if _container == 'default':
        if hasattr(proc, 'CONTAINER'):
            _container = proc.CONTAINER
            print('Using container: '+_container)

    timer = time.time()
    if _system_call:
        if _container is not None:
            raise Exception('Cannot use container with system call.')
        _container = ''
    else:
        if _system_call_prefix is not None:
            raise Exception(
                'Cannot use _system_call_prefix when _system_call=False')

    if _force_run is None:
        if os.environ.get('MLPROCESSORS_FORCE_RUN', '') == 'TRUE':
            _force_run = True
        else:
            _force_run = False

    if _keep_temp_files is None:
        if os.environ.get('MLPROCESSORS_KEEP_TEMP_FILES', '') == 'TRUE':
            _keep_temp_files = True
        else:
            _keep_temp_files = False

    # Execute a processor
    print('::::::::::::::::::::::::::::: '+proc.NAME)
    X = proc()  # instance
    ret = ProcessorExecuteOutput()  # We will return this object
    for input0 in proc.INPUTS:
        name0 = input0.name
        if name0 not in kwargs:
            raise Exception('Missing input: {}'.format(name0))
        setattr(X, name0, kwargs[name0])
    for output0 in proc.OUTPUTS:
        name0 = output0.name
        if name0 not in kwargs:
            raise Exception('Missing output: {}'.format(name0))
        setattr(X, name0, kwargs[name0])
    for param0 in proc.PARAMETERS:
        name0 = param0.name
        if name0 not in kwargs:
            if param0.optional:
                val0 = param0.default
            else:
                raise Exception('Missing required parameter: {}'.format(name0))
        else:
            val0 = kwargs[name0]
        setattr(X, name0, val0)
    if _cache:
        outputs_all_in_cairio = True
        output_signatures = dict()
        output_sha1s = dict()

        stats_signature0 = compute_processor_job_stats_signature(X)
        console_out_signature0 = compute_processor_job_console_out_signature(X)

        for output0 in proc.OUTPUTS:
            name0 = output0.name
            signature0 = compute_processor_job_output_signature(X, name0)
            output_signatures[name0] = signature0
            output_sha1 = ca.getValue(key=signature0, local_first=True)
            if output_sha1 is not None:
                print('Found output "{}" in cache.'.format(name0))
                output_sha1s[name0] = output_sha1

                # Do the following because if we have it locally,
                # we want to make sure it also gets propagated remotely
                # and vice versa
                ca.setValue(key=signature0, value=output_sha1, local_also=True)
            else:
                outputs_all_in_cairio = False
        output_files_all_found = False
        output_files = dict()
        if outputs_all_in_cairio:
            output_files_all_found = True
            for output0 in proc.OUTPUTS:
                out0 = getattr(X, name0)
                if out0:
                    name0 = output0.name
                    ext0 = _get_output_ext(out0)
                    sha1 = output_sha1s[name0]
                    output_files[name0] = 'sha1://'+sha1+'/'+name0+ext0
                    fname = ca.findFileBySha1(sha1=sha1)
                    if not fname:
                        output_files_all_found = False
        if outputs_all_in_cairio and (not output_files_all_found):
            print('Found job in cache, but not all output files exist.')

        if output_files_all_found:
            if not _force_run:
                print('Using outputs from cache.')

                for output0 in proc.OUTPUTS:
                    name0 = output0.name
                    fname1 = output_files[name0]
                    fname2 = getattr(X, name0)
                    if type(fname2) == str:
                        fname2 = os.path.abspath(fname2)
                        fname1 = ca.realizeFile(path=fname1)
                        if fname1 != fname2:
                            if os.path.exists(fname2):
                                os.remove(fname2)
                            print('copying file: {} -> {}'.format(fname1, fname2))
                            shutil.copyfile(fname1, fname2)
                        ret.outputs[name0] = fname2
                    else:
                        ret.outputs[name0] = fname1

                stats = ca.loadObject(key=stats_signature0, local_first=True)
                if stats:
                    ret.stats = stats

                console_out = ca.loadText(
                    key=console_out_signature0, local_first=True)
                if console_out:
                    ret.console_out = console_out
                return ret
            else:
                print('Found outputs in cache, but forcing run...')

    for input0 in proc.INPUTS:
        name0 = input0.name
        if hasattr(X, name0):
            val0 = getattr(X, name0)
            if input0.directory:
                val1 = val0
            else:
                val1 = ca.realizeFile(path=val0)
                if not val1:
                    raise Exception(
                        'Unable to realize input file {}: {}'.format(name0, val0))
            setattr(X, name0, val1)

    temporary_output_files = set()
    for output0 in proc.OUTPUTS:
        name0 = output0.name
        val0 = getattr(X, name0)
        job_signature0 = compute_processor_job_output_signature(X, None)
        if type(val0) != str:
            fname0 = job_signature0+'_'+name0+val0['ext']
            tmp_fname = create_temporary_file(fname0)
            temporary_output_files.add(tmp_fname)
            setattr(X, name0, tmp_fname)

    # Now it is time to execute
    start_time = time.time()
    if _container is None:
        print('MLPR EXECUTING::::::::::::::::::::::::::::: '+proc.NAME)
        console_capture = ConsoleCapture()
        console_capture.start_capturing()
        try:
            X.run()
        except:
            console_capture.stop_capturing()
            # clean up temporary output files
            print('Problem executing {}.'.format(proc.NAME))
            if _keep_temp_files:
                print('Not cleaning up files because _keep_temp_files was specified')
            else:
                print('Cleaning up {} files.'.format(
                    len(temporary_output_files)))
                for fname in temporary_output_files:
                    if os.path.exists(fname):
                        os.remove(fname)
            raise
        console_capture.stop_capturing()
        console_out = console_capture.consoleOut()
        print('MLPR FINISHED ::::::::::::::::::::::::::::: '+proc.NAME)
    else:
        # in a container
        container_path = ca.realizeFile(path=_container)
        if not container_path:
            raise Exception('Unable to realize container file: '+_container)
        tempdir = tempfile.mkdtemp()
        try:
            # Do not use cache inside container... we handle caching outside container
            console_out = _execute_in_container(proc, X, container=container_path, tempdir=tempdir, **kwargs, _cache=False,
                                                _force_run=True, _keep_temp_files=_keep_temp_files, _system_call_prefix=_system_call_prefix)
        except:
            if _keep_temp_files:
                print(
                    'Not removing temporary directory because _keep_temp_files was specified')
            else:
                shutil.rmtree(tempdir)
            raise
        if _keep_temp_files:
            print(
                'Not removing temporary directory because _keep_temp_files was specified')
        else:
            shutil.rmtree(tempdir)

    end_time = time.time()
    elapsed_time = end_time-start_time

    for output0 in proc.OUTPUTS:
        name0 = output0.name
        output_fname = getattr(X, name0)
        if output_fname in temporary_output_files:
            output_fname = ca.moveToLocalCache(output_fname)
        ret.outputs[name0] = output_fname
        if _cache:
            output_sha1 = ca.computeFileSha1(output_fname)
            signature0 = output_signatures[name0]
            ca.setValue(key=signature0, value=output_sha1, local_also=True)

    ret.stats['start_time'] = start_time
    ret.stats['end_time'] = end_time
    ret.stats['elapsed_sec'] = elapsed_time

    ret.console_out = console_out

    if _cache:
        ca.saveObject(key=stats_signature0, object=ret.stats, local_also=True)
        ca.saveText(key=console_out_signature0,
                    text=ret.console_out, local_also=True)

    return ret


def _get_output_ext(out0):
    if type(out0) == str:
        filename, ext = os.path.splitext(out0)
        return ext
    elif type(out0) == dict:
        if 'ext' in out0:
            return out0['ext']
    return ''

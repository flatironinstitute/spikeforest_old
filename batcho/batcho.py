from kbucket import client as kb
from pairio import client as pa
import random
import string
import os
import sys
import tempfile
import time
import subprocess
import traceback

_registered_commands = dict()


def register_job_command(*, command, prepare, run):
    _registered_commands[command] = dict(
        prepare=prepare,
        run=run
    )


def clear_batch_jobs(*, batch_name, job_index=None):
    batch = _retrieve_batch(batch_name)
    if not batch:
        return False
    jobs = batch['jobs']
    print('Batch has {} jobs.'.format(len(jobs)))

    num_cleared = 0
    for ii, job in enumerate(jobs):
        if (job_index is None) or (job_index == ii):
            command = job['command']
            label = job['label']
            status = _get_job_status(batch_name=batch_name, job_index=ii)
            if status:
                _set_job_status(batch_name=batch_name,
                                job_index=ii, status=None)
                _clear_job_lock(batch_name=batch_name, job_index=ii)
                num_cleared = num_cleared+1
    print('Cleared {} jobs.'.format(num_cleared))
    return True


def prepare_batch(*, batch_name, clear_jobs=False, job_index=None):
    batch = _retrieve_batch(batch_name)
    if not batch:
        return False
    jobs = batch['jobs']
    print('Batch has {} jobs.'.format(len(jobs)))

    num_prepared = 0
    for ii, job in enumerate(jobs):
        if (job_index is None) or (job_index == ii):
            command = job['command']
            label = job['label']
            status = _get_job_status(batch_name=batch_name, job_index=ii)
            if clear_jobs:
                if status:
                    _set_job_status(batch_name=batch_name,
                                    job_index=ii, status=None)
                    _clear_job_lock(batch_name=batch_name, job_index=ii)
                    status = None
            if (status != 'finished'):
                if command not in _registered_commands:
                    raise Exception(
                        'Problem preparing job {}: command not registered: {}'.format(label, command))
                X = _registered_commands[command]
                print('Preparing job {}'.format(label))
                try:
                    X['prepare'](job)
                except:
                    print('Error preparing job {}'.format(label))
                    raise
                num_prepared = num_prepared+1
                _set_job_status(batch_name=batch_name,
                                job_index=ii, status='ready')
                _clear_job_lock(batch_name=batch_name, job_index=ii)
    print('Prepared {} jobs.'.format(num_prepared))
    return True


def run_batch(*, batch_name, job_index=None):
    batch = _retrieve_batch(batch_name)
    if not batch:
        return False
    jobs = batch['jobs']
    print('Batch has {} jobs.'.format(len(jobs)))
    job_code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
    num_ran = 0
    for ii, job in enumerate(jobs):
        if (job_index is None) or (job_index == ii):
            command = job['command']
            label = job['label']
            status = _get_job_status(batch_name=batch_name, job_index=ii)
            if status == 'ready':
                if _acquire_job_lock(batch_name=batch_name, job_index=ii, code=job_code):
                    print('Acquired lock for job {}'.format(label))
                    if command not in _registered_commands:
                        raise Exception(
                            'Problem preparing job {}: command not registered: {}'.format(label, command))
                    _set_job_status(batch_name=batch_name,
                                    job_index=ii, status='running')
                    X = _registered_commands[command]
                    print('Running job {}'.format(label))

                    console_fname = _start_writing_to_file()

                    try:
                        result = X['run'](job)
                    except:
                        _stop_writing_to_file()

                        print('Error running job {}'.format(label))
                        _set_job_status(
                            batch_name=batch_name, job_index=ii, status='error', job_code=job_code)

                        _set_job_console_output(
                            batch_name=batch_name, job_index=ii, file_name=console_fname)
                        os.remove(console_fname)
                        raise
                    _stop_writing_to_file()

                    _set_job_status(batch_name=batch_name, job_index=ii,
                                    status='finished', job_code=job_code)
                    _set_job_result(
                        batch_name=batch_name, job_index=ii, result=result, job_code=job_code)

                    _set_job_console_output(
                        batch_name=batch_name, job_index=ii, file_name=console_fname)
                    os.remove(console_fname)

                    num_ran = num_ran+1

    print('Ran {} jobs.'.format(num_ran))
    return True


def assemble_batch(*, batch_name):
    batch = _retrieve_batch(batch_name)
    if not batch:
        return False
    jobs = batch['jobs']
    print('Batch has {} jobs.'.format(len(jobs)))
    num_ran = 0
    assembled_results = []
    for ii, job in enumerate(jobs):
        command = job['command']
        label = job['label']
        status = _get_job_status(batch_name=batch_name, job_index=ii)
        if status == 'finished':
            print('ASSEMBLING job result for {}'.format(label))
            result = _get_job_result(batch_name=batch_name, job_index=ii)
            assembled_results.append(dict(
                job=job,
                result=result
            ))
        else:
            raise Exception(
                'Job {} not finished. Status is {}'.format(label, status))
    print('Assembling {} results'.format(len(assembled_results)))
    kb.saveObject(key=dict(name='batcho_batch_results',
                           batch_name=batch_name), object=dict(results=assembled_results))
    return True


def get_batch_jobs(*, batch_name):
    batch = _retrieve_batch(batch_name)
    if not batch:
        return None
    jobs = batch['jobs']
    return jobs


def get_batch_job_statuses(*, batch_name, job_index=None):
    batch = _retrieve_batch(batch_name)
    if not batch:
        return None
    jobs = batch['jobs']
    ret = []
    for ii, job in enumerate(jobs):
        if (job_index is None) or (job_index == ii):
            status = _get_job_status(batch_name=batch_name, job_index=ii)
            ret.append(dict(
                job=job,
                status=status
            ))
    return ret


def set_batch(*, batch_name, jobs, compute_resource=None):
    key = dict(name='batcho_batch', batch_name=batch_name)
    kb.saveObject(key=key, object=dict(jobs=jobs))
    if compute_resource is not None:
        add_batch_name_for_compute_resource(compute_resource, batch_name)


def add_batch_name_for_compute_resource(compute_resource, batch_name):
    key0 = dict(
        name='compute_resource_batch_names',
        compute_resource=compute_resource
    )
    while True:
        obj = kb.loadObject(key=key0)
        if not obj:
            obj = dict(batch_names=[])
        if batch_name in obj['batch_names']:
            return
        obj['batch_names'].append(batch_name)
        kb.saveObject(key=key0, object=obj)
        # loop through and check again ## Note: there is still a possibility of failure/conflict here -- use locking in future
        time.sleep(0.2)


def remove_batch_name_for_compute_resource(compute_resource, batch_name):
    key0 = dict(
        name='compute_resource_batch_names',
        compute_resource=compute_resource
    )
    while True:
        obj = kb.loadObject(key=key0)
        if not obj:
            obj = dict(batch_names=[])
        if batch_name not in obj['batch_names']:
            return
        obj['batch_names'].remove(batch_name)
        kb.saveObject(key=key0, object=obj)
        # loop through and check again ## Note: there is still a possibility of failure/conflict here -- use locking in future
        time.sleep(0.2)


def _call_run_batch(batch_name, run_prefix):
    source_dir = os.path.dirname(os.path.realpath(__file__))
    if run_prefix is None:
        run_prefix = ''
    if run_prefix:
        run_prefix = run_prefix+' '
    cmd = '{}python {}/internal_batcho_run.py {}'.format(
        run_prefix, source_dir, batch_name)
    try:
        ret_code = _run_command_and_print_output(cmd)
    except:
        print('Error running batch: ', err)
        return False
    if ret_code != 0:
        print('Run batch command returned non-zero exit code.')
        return False
    return True


def _shell_execute(cmd):
    popen = subprocess.Popen('{}'.format(cmd), stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, universal_newlines=True, shell=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        # yield stdout_line
        print(stdout_line, end='\r')
    popen.stdout.close()
    return_code = popen.wait()
    return return_code


def _run_command_and_print_output(cmd):
    print('RUNNING: '+cmd)
    return _shell_execute(cmd)


def _try_handle_batch(compute_resource, batch_name, run_prefix):
    if not _retrieve_batch(batch_name):
        # In this case the object is not yet ready, so just return false and do not remove
        return False
    try:
        if not prepare_batch(batch_name=batch_name, clear_jobs=True):
            raise Exception('Problem preparing batch.')
        if not _call_run_batch(batch_name=batch_name, run_prefix=run_prefix):
            raise Exception('Problem running batch.')
        if not assemble_batch(batch_name=batch_name):
            raise Exception('Problem assembling batch.')
    except Exception as err:
        remove_batch_name_for_compute_resource(
            compute_resource, batch_name=batch_name)
        print('Error handling batch: ', err)
        return False
    remove_batch_name_for_compute_resource(
        compute_resource, batch_name=batch_name)
    return True


def listen_as_compute_resource(compute_resource, run_prefix=None):
    index = 0
    while True:
        batch_names = get_batch_names_for_compute_resource(compute_resource)
        if len(batch_names) > 0:
            if index >= len(batch_names):
                index = 0
            batch_name = batch_names[index]
            _try_handle_batch(compute_resource, batch_name,
                              run_prefix=run_prefix)
            index = index+1
        time.sleep(4)


def get_batch_names_for_compute_resource(compute_resource):
    key0 = dict(
        name='compute_resource_batch_names',
        compute_resource=compute_resource
    )
    obj = kb.loadObject(key=key0)
    if not obj:
        obj = dict(batch_names=[])
    return obj.get('batch_names', [])


def get_batch_results(*, batch_name):
    key = dict(name='batcho_batch_results', batch_name=batch_name)
    return kb.loadObject(key=key)


def get_batch_job_console_output(*, batch_name, job_index, return_url=False, verbose=False):
    key = dict(name='batcho_job_console_output',
               batch_name=batch_name, job_index=job_index)
    if return_url:
        url = kb.findFile(key=key, local=False, remote=True)
        return url
    else:
        fname = kb.realizeFile(key=key, verbose=verbose)
        if not fname:
            return None
        txt =_read_text_file(fname)
        return txt


def _retrieve_batch(batch_name):
    print('Retrieving batch {}'.format(batch_name))
    key = dict(name='batcho_batch', batch_name=batch_name)
    a = pa.get(key=key)
    if not a:
        print('Unable to retrieve batch {}. Not found in pairio.'.format(batch_name))
        return None
    obj = kb.loadObject(key=key)
    if not obj:
        print(
            'Unable to retrieve batch {}. Object not found on kbucket.'.format(batch_name))
        return None
    if 'jobs' not in obj:
        raise Exception(
            'batch object does not contain jobs field for batch_name={}'.format(batch_name))
    return obj


def _get_job_status(*, batch_name, job_index):
    key = dict(name='batcho_job_status',
               batch_name=batch_name, job_index=job_index)
    return pa.get(key=key)


def _set_job_status(*, batch_name, job_index, status, job_code=None):
    if job_code:
        code = _get_job_lock_code(batch_name=batch_name, job_index=job_index)
        if code != job_code:
            print('Not setting job status because lock code does not match batch code')
            return
    key = dict(name='batcho_job_status',
               batch_name=batch_name, job_index=job_index)
    return pa.set(key=key, value=status)


def _get_job_result(*, batch_name, job_index):
    key = dict(name='batcho_job_result',
               batch_name=batch_name, job_index=job_index)
    return kb.loadObject(key=key)


def _set_job_result(*, batch_name, job_index, result, job_code=None):
    if job_code:
        code = _get_job_lock_code(batch_name=batch_name, job_index=job_index)
        if code != job_code:
            print('Not setting job result because lock code does not match job code')
            return
    key = dict(name='batcho_job_result',
               batch_name=batch_name, job_index=job_index)
    return kb.saveObject(key=key, object=result)


def _set_job_console_output(*, batch_name, job_index, file_name, job_code=None):
    if job_code:
        code = _get_job_lock_code(batch_name=batch_name, job_index=job_index)
        if code != job_code:
            print(
                'Not setting job console output because lock code does not match job code')
            return
    key = dict(name='batcho_job_console_output',
               batch_name=batch_name, job_index=job_index)
    return kb.saveFile(key=key, fname=file_name)


def _acquire_job_lock(*, batch_name, job_index, code):
    key = dict(name='batcho_job_lock',
               batch_name=batch_name, job_index=job_index)
    return pa.set(key=key, value=code, overwrite=False)


def _get_job_lock_code(*, batch_name, job_index):
    key = dict(name='batcho_job_lock',
               batch_name=batch_name, job_index=job_index)
    return pa.get(key=key)


def _clear_job_lock(*, batch_name, job_index):
    key = dict(name='batcho_job_lock',
               batch_name=batch_name, job_index=job_index)
    pa.set(key=key, value=None, overwrite=True)


def _read_text_file(fname):
    with open(fname, 'r') as f:
        return f.read()


_console_to_file_data = dict(
    file_handle=None,
    file_name=None,
    original_stdout=sys.stdout,
    original_stderr=sys.stderr
)


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


def _start_writing_to_file():
    if _console_to_file_data['file_name']:
        _stop_writing_to_file()
    tmp_fname = tempfile.mktemp(suffix='.txt')
    file_handle = open(tmp_fname, 'w')
    _console_to_file_data['file_name'] = tmp_fname
    _console_to_file_data['file_handle'] = file_handle
    sys.stdout = Logger2(file_handle, _console_to_file_data['original_stdout'])
    sys.stderr = Logger2(file_handle, _console_to_file_data['original_stderr'])
    return tmp_fname


def _stop_writing_to_file():
    sys.stdout = _console_to_file_data['original_stdout']
    sys.stderr = _console_to_file_data['original_stderr']
    fname = _console_to_file_data['file_name']
    file_handle = _console_to_file_data['file_handle']

    if not fname:
        return
    file_handle.close()
    _console_to_file_data['file_name'] = None
    _console_to_file_data['file_handle'] = None

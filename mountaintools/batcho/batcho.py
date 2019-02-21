from cairio import client as ca
import random
import string
import os
import sys
import tempfile
import time
import subprocess
import traceback
import multiprocessing
import numpy as np

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
    batch_label = batch.get('label', 'unknown')
    jobs = batch['jobs']
    print('Batch ({}) has {} jobs.'.format(batch_label, len(jobs)))

    num_cleared = 0
    for ii, job in enumerate(jobs):
        if (job_index is None) or (job_index == ii):
            command = job['command']
            job_label = job['label']
            status = _get_job_status(batch_name=batch_name, job_index=ii)
            if status:
                _set_job_status(batch_name=batch_name,
                                job_index=ii, status=None)
                _clear_job_lock(batch_name=batch_name, job_index=ii)
                num_cleared = num_cleared+1
    print('Cleared {} jobs for batch: {}.'.format(num_cleared, batch_label))
    return True


def prepare_batch(*, batch_name, clear_jobs=False, job_index=None):
    batch_code = _get_batch_code(batch_name)
    if not batch_code:
        raise Exception(
            'Unable to get batch code for batch {}'.format(batch_name))

    _set_batch_status(batch_name=batch_name, status=dict(status='preparing'))
    batch = _retrieve_batch(batch_name)
    if not batch:
        _set_batch_status(batch_name=batch_name, status=dict(
            status='error', error='Unable to retrieve batch in prepare_batch.'))
        return False
    batch_label = batch.get('label', 'unknown')
    jobs = batch['jobs']
    print('Batch ({}) has {} jobs.'.format(batch_label, len(jobs)))

    num_prepared = 0
    for ii, job in enumerate(jobs):
        if (job_index is None) or (job_index == ii):
            _set_batch_status(batch_name=batch_name, status=dict(
                status='preparing', job_index=ii))
            command = job['command']
            job_label = job['label']
            status = _get_job_status(batch_name=batch_name, job_index=ii)
            if clear_jobs:
                if status:
                    _set_job_status(batch_name=batch_name,
                                    job_index=ii, status=None)
                    _clear_job_lock(batch_name=batch_name, job_index=ii)
                    status = None
            if (status != 'finished'):
                if command not in _registered_commands:
                    _set_batch_status(batch_name=batch_name, status=dict(
                        status='error', job_index=ii, error='Command not registerd.'))
                    raise Exception(
                        'Problem preparing job {}: command not registered: {}'.format(job_label, command))
                X = _registered_commands[command]
                print('Preparing job {} in batch:'.format(
                    job_label, batch_label))
                _check_batch_code(batch_name, batch_code)
                try:
                    X['prepare'](job)
                except:
                    _set_batch_status(batch_name=batch_name, status=dict(
                        status='error', job_index=ii, error='Error preparing job.'))
                    print('Error preparing job {}'.format(job_label))
                    raise
                _check_batch_code(batch_name, batch_code)
                num_prepared = num_prepared+1
                _set_job_status(batch_name=batch_name,
                                job_index=ii, status=dict(status='ready'))
                _clear_job_lock(batch_name=batch_name, job_index=ii)
    _check_batch_code(batch_name, batch_code)
    _set_batch_status(batch_name=batch_name,
                      status=dict(status='done_preparing'))
    _init_next_batch_job_index_to_run(batch_name=batch_name)
    print('Prepared {} jobs for batch: {}'.format(num_prepared, batch_label))
    return True


def _init_next_batch_job_index_to_run(*, batch_name):
    key = dict(name='batcho_next_batch_job_index_to_run',
               batch_name=batch_name)
    ca.setValue(key=key, value=str(0))


def _take_next_batch_job_index_to_run(*, batch_name):
    key = dict(name='batcho_next_batch_job_index_to_run',
               batch_name=batch_name)
    last_attempted_job_index = -1
    last_attempted_job_index_timestamp = time.time()
    while True:
        val = ca.getValue(key=key)
        if val is None:
            return None
        job_index = int(val)
        if _acquire_job_lock(batch_name=batch_name, job_index=job_index):
            ca.setValue(key=key, value=str(job_index+1))
            return job_index
        else:
            if job_index == last_attempted_job_index:
                elapsed0 = time.time()-last_attempted_job_index_timestamp
                if elapsed0 > 10:
                    raise Exception('Unexpected problem where we cannot obtain the job lock, and yet the current job index remains at {} for {} seconds.'.format(
                        job_index, elapsed0))
            last_attempted_job_index = job_index
            last_attempted_job_index_timestamp = time.time()
            time.sleep(random.uniform(0, 2))


def run_batch(*, batch_name, job_index=None):
    batch_code = _get_batch_code(batch_name)
    if not batch_code:
        raise Exception(
            'Unable to get batch code for batch {}'.format(batch_name))

    batch = _retrieve_batch(batch_name)
    if not batch:
        return False
    batch_label = batch.get('label', 'unknown')
    jobs = batch['jobs']
    print('RUN: Batch ({}) has {} jobs.'.format(batch_label, len(jobs)))

    while True:
        ii = _take_next_batch_job_index_to_run(batch_name=batch_name)
        if (ii is None) or (ii >= len(jobs)):
            break
        job = jobs[ii]
        num_ran = 0
        if (job_index is None) or (job_index == ii):
            _check_batch_code(batch_name, batch_code)

            command = job['command']
            job_label = job['label']
            status = _get_job_status_string(
                batch_name=batch_name, job_index=ii)
            if status == 'ready':
                print('Running job {} in batch: {}'.format(
                    job_label, batch_label))
                if command not in _registered_commands:
                    raise Exception(
                        'Problem preparing job {}: command not registered: {}'.format(job_label, command))
                _set_job_status(batch_name=batch_name,
                                job_index=ii, status=dict(status='running'))
                X = _registered_commands[command]
                print('Running job {} in batch: {}'.format(
                    job_label, batch_label))

                console_fname = _start_writing_to_file()

                _check_batch_code(batch_name, batch_code)
                try:
                    result = X['run'](job)
                except:
                    _stop_writing_to_file()

                    print('Error running job {}'.format(job_label))
                    _set_job_status(
                        batch_name=batch_name, job_index=ii, status=dict(status='error'))

                    _set_job_console_output(
                        batch_name=batch_name, job_index=ii, file_name=console_fname)
                    os.remove(console_fname)
                    raise
                _stop_writing_to_file()
                _check_batch_code(batch_name, batch_code)

                _set_job_status(batch_name=batch_name, job_index=ii,
                                status=dict(status='finished'))
                _set_job_result(
                    batch_name=batch_name, job_index=ii, result=result)

                _set_job_console_output(
                    batch_name=batch_name, job_index=ii, file_name=console_fname)
                os.remove(console_fname)

                num_ran = num_ran+1

    _check_batch_code(batch_name, batch_code)
    #print('Ran {} jobs.'.format(num_ran))
    return True


def assemble_batch(*, batch_name):
    batch_code = _get_batch_code(batch_name)
    if not batch_code:
        raise Exception(
            'Unable to get batch code for batch {}'.format(batch_name))

    _set_batch_status(batch_name=batch_name, status=dict(status='assembling'))
    batch = _retrieve_batch(batch_name)
    if not batch:
        _set_batch_status(batch_name=batch_name, status=dict(
            status='error', error='Unable to retrieve batch in assemble_batch.'))
        return False
    batch_label = batch.get('label', 'unknown')
    jobs = batch['jobs']
    print('Batch ({}) has {} jobs.'.format(batch_label, len(jobs)))
    status_strings = get_batch_job_statuses(batch_name=batch_name)
    assembled_results = []
    for ii, job in enumerate(jobs):
        _check_batch_code(batch_name, batch_code)
        _set_batch_status(batch_name=batch_name, status=dict(
            status='assembling', job_index=ii))
        command = job['command']
        job_label = job['label']

        # there is sometimes a mysterious error here....
        status_string = status_strings.get(str(ii), None)
        if status_string == 'finished':
            print('ASSEMBLING job result for {}'.format(job_label))
            result = _get_job_result(batch_name=batch_name, job_index=ii)
            assembled_results.append(dict(
                job=job,
                result=result
            ))
        else:
            errstr = 'Problem assembling job {}. Status is {}.'.format(
                ii, status_string)

            _set_batch_status(batch_name=batch_name, status=dict(
                status='error', error=errstr))
            raise Exception(errstr)

    _check_batch_code(batch_name, batch_code)
    print('Assembling {} results'.format(len(assembled_results)))
    ca.saveObject(key=dict(name='batcho_batch_results', batch_name=batch_name),
                  object=dict(results=assembled_results), confirm=True)
    _set_batch_status(batch_name=batch_name,
                      status=dict(status='done_assembling'))
    return True


def get_batch_jobs(*, batch_name):
    batch = _retrieve_batch(batch_name)
    if not batch:
        return None
    jobs = batch['jobs']
    return jobs


def get_batch_job_statuses(*, batch_name, job_index=None):
    key = dict(name='batcho_job_status_strings',
               batch_name=batch_name)
    obj = ca.getValue(key=key, subkey='-', parse_json=True)
    if not obj:
        return dict()
    return obj
    # batch = _retrieve_batch(batch_name)
    # if not batch:
    #     return None
    # jobs = batch['jobs']
    # ret = []
    # for ii, job in enumerate(jobs):
    #     if (job_index is None) or (job_index == ii):
    #         status = _get_job_status(batch_name=batch_name, job_index=ii)
    #         ret.append(dict(
    #             job=job,
    #             status=status
    #         ))
    # return ret


def _get_job_status_string(*, batch_name, job_index):
    key = dict(name='batcho_job_status_strings',
               batch_name=batch_name)
    return ca.getValue(key=key, subkey=str(job_index))


def stop_batch(*, batch_name):
    status0 = get_batch_status(batch_name=batch_name)
    if status0 is not None:
        if status0['status'] not in ['finished', 'error']:
            batch_code = 'batch_code_force_stop'
            ca.setValue(key=dict(name='batcho_batch_code',
                                 batch_name=batch_name), value=batch_code)
            _set_batch_status(batch_name=batch_name, status=dict(
                status='error', error='force stopped'))


def _get_batch_code(batch_name):
    return ca.getValue(key=dict(name='batcho_batch_code', batch_name=batch_name))


def _check_batch_code(batch_name, batch_code):
    code2 = _get_batch_code(batch_name)
    if not code2:
        raise Exception(
            'Unable to get batch code for batch {}'.format(batch_name))
    if batch_code != code2:
        raise Exception('Batch codes do not match for batch {}. Perhaps the batch was canceled or restarted. ({} <> {})'.format(
            batch_name, batch_code, code2))


def _set_batch_code(batch_name, batch_code):
    ca.setValue(key=dict(name='batcho_batch_code',
                         batch_name=batch_name), value=batch_code)


def set_batch(*, batch_name, jobs, label=None, compute_resource=None):
    if label is None:
        label = batch_name
    status0 = get_batch_status(batch_name=batch_name)
    if status0 is not None:
        if status0['status'] not in ['finished', 'error']:
            raise Exception('Unable to set batch. Batch status already exists for {}: {}'.format(
                batch_name, status0))

    _set_batch_status(batch_name=batch_name,
                      status=dict(status='initializing'))

    # set a new batch code
    batch_code = 'batch_code_'+_random_string(10)
    _set_batch_code(batch_name, batch_code)

    # set the batch
    key = dict(name='batcho_batch', batch_name=batch_name)
    ca.saveObject(key=key, object=dict(label=label, jobs=jobs))

    _set_batch_status(batch_name=batch_name, status=dict(status='initialized'))

    if compute_resource is not None:
        clear_batch_jobs(batch_name=batch_name)
        add_batch_name_for_compute_resource(compute_resource, batch_name)


def add_batch_name_for_compute_resource(compute_resource, batch_name):
    key0 = dict(
        name='compute_resource_batch_names',
        compute_resource=compute_resource
    )
    return ca.setValue(key=key0, subkey=batch_name, value='dummy_val')
    # while True:
    #     obj = ca.loadObject(key=key0)
    #     if not obj:
    #         obj = dict(batch_names=[])
    #     if batch_name in obj['batch_names']:
    #         return
    #     obj['batch_names'].append(batch_name)
    #     ca.saveObject(key=key0, object=obj)
    #     # loop through and check again ## Note: there is still a possibility of failure/conflict here -- use locking in future
    #     time.sleep(0.2)


def remove_batch_name_for_compute_resource(compute_resource, batch_name):
    key0 = dict(
        name='compute_resource_batch_names',
        compute_resource=compute_resource
    )
    return ca.setValue(key=key0, subkey=batch_name, value=None)

    # while True:
    #     obj = ca.loadObject(key=key0)
    #     if not obj:
    #         obj = dict(batch_names=[])
    #     if batch_name not in obj['batch_names']:
    #         return
    #     obj['batch_names'].remove(batch_name)
    #     ca.saveObject(key=key0, object=obj)
    #     # loop through and check again ## Note: there is still a possibility of failure/conflict here -- use locking in future
    #     time.sleep(0.2)


def _helper_call_run_batch(a):
    return _call_run_batch(**a)


def _call_run_batch(batch_name, run_prefix, num_simultaneous=None):
    if num_simultaneous is not None:
        print('Running in parallel (num_simultaneous={}).'.format(num_simultaneous))
        pool = multiprocessing.Pool(num_simultaneous)
        results = pool.map(_helper_call_run_batch, [dict(
            batch_name=batch_name, run_prefix=run_prefix, num_simultaneous=None) for i in range(num_simultaneous)])
        pool.close()
        pool.join()
        for result in results:
            if not result:
                return result
        return True

    source_dir = os.path.dirname(os.path.realpath(__file__))
    if run_prefix is None:
        run_prefix = ''
    if run_prefix:
        run_prefix = run_prefix+' '
    opts = []
    cmd = '{}python {}/internal_batcho_run.py {} {}'.format(
        run_prefix, source_dir, batch_name, ' '.join(opts))

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


def _try_handle_batch(compute_resource, batch_name, run_prefix, num_simultaneous=None, allow_uncontainerized=False):
    batch = _retrieve_batch(batch_name)
    if not batch:
        # In this case the object is not yet ready, so just return false and do not remove
        return False
    batch_label = batch.get('label', 'unknown')
    try:
        batch_code = _get_batch_code(batch_name)
        if not batch_code:
            raise Exception(
                'Unable to get batch code for batch {} ({})'.format(batch_name, batch_label))

        _set_batch_status(batch_name=batch_name,
                          status=dict(status='checking'))
        jobs = batch['jobs']
        for ii, job in enumerate(jobs):
            container = job.get('container', '')
            if (not allow_uncontainerized) and (not container):
                raise Exception(
                    'Unable to run uncontainerized job. Specify a container in the job spec or use the --allow_uncontainerized flag on the compute resource.')

        _set_batch_status(batch_name=batch_name,
                          status=dict(status='preparing'))
        if not prepare_batch(batch_name=batch_name, clear_jobs=True):
            raise Exception('Problem preparing batch.')
        _check_batch_code(batch_name, batch_code)

        _set_batch_status(batch_name=batch_name, status=dict(status='running'))
        if not _call_run_batch(batch_name=batch_name, run_prefix=run_prefix, num_simultaneous=num_simultaneous):
            raise Exception('Problem running batch.')
        _check_batch_code(batch_name, batch_code)

        _set_batch_status(batch_name=batch_name,
                          status=dict(status='assembling'))
        if not assemble_batch(batch_name=batch_name):
            raise Exception('Problem assembling batch.')
        _check_batch_code(batch_name, batch_code)

        _set_batch_status(batch_name=batch_name,
                          status=dict(status='finished'))
    except Exception as err:
        _set_batch_status(batch_name=batch_name, status=dict(
            status='error', error='Error handling batch: {}'.format(err)))
        remove_batch_name_for_compute_resource(
            compute_resource, batch_name=batch_name)
        traceback.print_exc()
        print('Error handling batch: ', err)

        return False
    remove_batch_name_for_compute_resource(
        compute_resource, batch_name=batch_name)
    return True


def listen_as_compute_resource(compute_resource, run_prefix=None, num_simultaneous=None, allow_uncontainerized=False):
    _clear_batch_names_for_compute_resource(compute_resource)
    index = 0
    while True:
        batch_names = get_batch_names_for_compute_resource(compute_resource)
        if len(batch_names) > 0:
            if index >= len(batch_names):
                index = 0
            batch_name = batch_names[index]
            _try_handle_batch(compute_resource, batch_name,
                              run_prefix=run_prefix, num_simultaneous=num_simultaneous, allow_uncontainerized=allow_uncontainerized)
            index = index+1
        time.sleep(4)


def get_batch_names_for_compute_resource(compute_resource):
    key0 = dict(
        name='compute_resource_batch_names',
        compute_resource=compute_resource
    )
    obj = ca.getValue(key=key0, subkey='-', parse_json=True)
    if not obj:
        return []
    batch_names = list(obj.keys())
    return batch_names


def _clear_batch_names_for_compute_resource(compute_resource):
    print('Clearing batch names for compute resource: '+compute_resource)
    key0 = dict(
        name='compute_resource_batch_names',
        compute_resource=compute_resource
    )
    obj = ca.setValue(key=key0, subkey='-', value=None)
    print('-----------------------',
          get_batch_names_for_compute_resource(compute_resource))


def get_batch_results(*, batch_name):
    key = dict(name='batcho_batch_results', batch_name=batch_name)
    return ca.loadObject(key=key)


def get_batch_job_console_output(*, batch_name, job_index):
    key = dict(name='batcho_job_console_output',
               batch_name=batch_name, job_index=job_index)
    return ca.loadText(key=key)

    # if return_url:
    #     url = ca.findFile(key=key, local=False, remote=True)
    #     return url
    # else:
    #     fname = kb.realizeFile(key=key, verbose=verbose)
    #     if not fname:
    #         return None
    #     txt = _read_text_file(fname)
    #     return txt


def _retrieve_batch(batch_name):
    print('Retrieving batch {}'.format(batch_name))
    key = dict(name='batcho_batch', batch_name=batch_name)
    a = ca.getValue(key=key)
    if not a:
        print('Unable to retrieve batch {}. Not found in pairio.'.format(batch_name))
        return None
    obj = ca.loadObject(key=key)
    if not obj:
        print(
            'Unable to retrieve batch {}. Object not found on kbucket.'.format(batch_name))
        return None
    if 'jobs' not in obj:
        raise Exception(
            'batch object does not contain jobs field for batch_name={}'.format(batch_name))
    return obj


def _get_job_status(*, batch_name, job_index):
    key = dict(name='batcho_job_statuses',
               batch_name=batch_name)
    subkey = str(job_index)
    return ca.loadObject(key=key, subkey=subkey)


def _set_job_status(*, batch_name, job_index, status):
    # if job_code:
    #    code = _get_job_lock_code(batch_name=batch_name, job_index=job_index)
    #    if code != job_code:
    #        print('Not setting job status because lock code does not match batch code')
    #        return
    status_string = None
    if status:
        status_string = status.get('status', None)

    key = dict(name='batcho_job_statuses',
               batch_name=batch_name)
    subkey = str(job_index)
    if not ca.saveObject(key=key, subkey=subkey, object=status):
        return False

    key = dict(name='batcho_job_status_strings',
               batch_name=batch_name)
    subkey = str(job_index)
    if not ca.setValue(key=key, subkey=subkey, value=status_string):
        print('WARNING: problem setting batch job status for subkey {}: {}'.format(
            subkey, status_string))
        return False
    return True


def get_batch_status(*, batch_name):
    key = dict(name='batcho_batch_status',
               batch_name=batch_name)
    return ca.loadObject(key=key)


def _set_batch_status(*, batch_name, status):
    key = dict(name='batcho_batch_status',
               batch_name=batch_name)
    return ca.saveObject(key=key, object=status)


def _get_job_result(*, batch_name, job_index):
    key = dict(name='batcho_job_result',
               batch_name=batch_name, job_index=job_index)
    return ca.loadObject(key=key)


def _set_job_result(*, batch_name, job_index, result):
    key = dict(name='batcho_job_result',
               batch_name=batch_name, job_index=job_index)
    return ca.saveObject(key=key, object=result, confirm=True)


def _set_job_console_output(*, batch_name, job_index, file_name):
    key = dict(name='batcho_job_console_output',
               batch_name=batch_name, job_index=job_index)
    return ca.saveFile(key=key, path=file_name)


def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))


def _acquire_job_lock(*, batch_name, job_index):
    key = dict(name='batcho_job_lock',
               batch_name=batch_name, job_index=job_index)
    code = 'lock_'+_random_string(10)
    return ca.setValue(key=key, value=code, overwrite=False)


# def _get_job_lock_code(*, batch_name, job_index):
#    key = dict(name='batcho_job_lock',
#               batch_name=batch_name, job_index=job_index)
#    return ca.getValue(key=key)


def _clear_job_lock(*, batch_name, job_index):
    key = dict(name='batcho_job_lock',
               batch_name=batch_name, job_index=job_index)
    ca.setValue(key=key, value=None, overwrite=True)


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

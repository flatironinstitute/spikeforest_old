import os
import json
import multiprocessing
import random
import time
from mountainclient import client as mt
from mountainclient import MountainClient
from .computeresourceclient import ComputeResourceClient
from .shellscript import ShellScript
from .temporarydirectory import TemporaryDirectory
from .mountainjob import MountainJob
from .mountainjob import MountainJobResult

# module global
_realized_files = set()
_compute_resources_config = dict()

def configComputeResource(name, *, resource_name, collection=None, share_id=None):
    if resource_name is not None:
        _compute_resources_config[name]=dict(
            resource_name=resource_name,
            collection=collection,
            share_id=share_id
        )
    else:
        _compute_resources_config[name] = None

def executeBatch(*, jobs, label='', num_workers=None, compute_resource=None, halt_key=None, job_status_key=None, job_result_key=None, srun_opts=None, job_index_file=None):
    if len(jobs) == 0:
        return []

    if num_workers is not None:
        if compute_resource is not None:
            raise Exception('Cannot specify both num_workers and compute_resource in executeBatch.')
        if srun_opts is not None:
            raise Exception('Cannot specify both num_workers and srun_opts in executeBatch.')
        if job_index_file is not None:
            raise Exception('Cannot specify both num_workers and job_index_file in executeBatch.')
    if compute_resource is not None:
        if srun_opts is not None:
            raise Exception('Cannot specify both compute_resource and srun_opts in executeBatch.')
        if job_index_file is not None:
            raise Exception('Cannot specify both compute_resource and job_index_file in executeBatch.')
    if srun_opts is not None:
        if job_index_file is not None:
            raise Exception('Cannot specify both srun_opts and job_index_file in executeBatch.')

    if type(compute_resource)==str:
        if compute_resource in _compute_resources_config:
            compute_resource=_compute_resources_config[compute_resource]
        else:
            raise Exception('No compute resource named {}. Use mlprocessors.configComputeResource("{}",...).'.format(compute_resource, compute_resource))

    if type(compute_resource)==dict:
        if compute_resource['resource_name'] is None:
            compute_resource = None

    if compute_resource:
        for job in jobs:
            job.useRemoteUrlsForInputFiles()

    files_to_realize = []
    for job in jobs:
        files_to_realize.extend(job.getFilesToRealize())
    files_to_realize = list(set(files_to_realize))

    local_client = MountainClient()

    if compute_resource:
        print('Ensuring files are available on remote server...')
        for fname in files_to_realize:
            if fname.startswith('sha1://'):
                if local_client.findFile(path=fname):
                    mt.saveFile(path=fname)
            elif fname.startswith('kbucket://'):
                pass
            else:
                mt.saveFile(path=fname)

        CRC=ComputeResourceClient(**compute_resource)
        batch_id = CRC.initializeBatch(jobs=jobs, label=label)
        CRC.startBatch(batch_id=batch_id)
        try:
            CRC.monitorBatch(batch_id=batch_id)
        except:
            CRC.stopBatch(batch_id=batch_id)
            raise

        results = CRC.getBatchJobResults(batch_id=batch_id)
        if results is None:
            raise Exception('Unable to get batch results.')
        for i, job in enumerate(jobs):
            result0 = results[i]
            if result0 is None:
                raise Exception('Unexpected: Unable to find result for job.')
            job.result = result0
        return results

    # Not using compute resource, do this locally

    print('Making sure files are available on local computer...')
    for fname in files_to_realize:
        print('Realizing {}...'.format(fname))
        mt.realizeFile(path=fname)

    if srun_opts is None:
        for job_index, job in enumerate(jobs):
            setattr(job, 'halt_key', halt_key)
            setattr(job, 'job_status_key', job_status_key)
            setattr(job, 'job_index', job_index)
            setattr(job, 'job_result_key', job_result_key)

        if num_workers is not None:
            pool = multiprocessing.Pool(num_workers)
            results = pool.map(_execute_job, jobs)
            pool.close()
            pool.join()
        else:
            results = []
            if job_index_file is None:
                for job in jobs:
                    results.append(_execute_job(job))
            else:
                while True:
                    job_index = _take_next_batch_job_index_to_run(job_index_file)
                    if job_index < len(jobs):
                        _execute_job(jobs[job_index])
                    else:
                        break
                return None
                    
        for i, job in enumerate(jobs):
            job.result = results[i]
    else:
        # using srun
        keep_temp_files = True
        with TemporaryDirectory(remove=(not keep_temp_files)) as temp_path:
            local_client = MountainClient()
            job_objects = [job.getObject() for job in jobs]
            jobs_path=os.path.join(temp_path, 'jobs.json')
            job_index_file=os.path.join(temp_path, 'job_index.txt')
            with open(job_index_file, 'w') as f:
                f.write('0')
            local_client.saveObject(job_objects, dest_path=jobs_path)
            if job_result_key is None:
                job_result_key = dict(
                    name='executebatch_job_result',
                    randid=_random_string(8)
                )
            srun_py_script = ShellScript("""
                #!/usr/bin/env python

                from mlprocessors import executeBatch
                from mountaintools import MountainClient
                from mlprocessors import MountainJob

                local_client = MountainClient()

                job_objects = local_client.loadObject(path = '{jobs_path}')
                jobs = [MountainJob(job_object=obj) for obj in job_objects]

                executeBatch(jobs=jobs, label='{label}', num_workers=None, compute_resource=None, halt_key={halt_key}, job_status_key={job_status_key}, job_result_key={job_result_key}, srun_opts=None, job_index_file='{job_index_file}')
            """, script_path=os.path.join(temp_path, 'execute_batch_srun.py'), keep_temp_files=keep_temp_files)
            srun_py_script.substitute('{jobs_path}', jobs_path)
            srun_py_script.substitute('{label}', label)
            if halt_key:
                srun_py_script.substitute('{halt_key}', json.dumps(halt_key))
            else:
                srun_py_script.substitute('{halt_key}', 'None')
            if job_status_key:
                srun_py_script.substitute('{job_status_key}', json.dumps(job_status_key))
            else:
                srun_py_script.substitute('{job_status_key}', 'None')
            if job_result_key:
                srun_py_script.substitute('{job_result_key}', json.dumps(job_result_key))
            else:
                srun_py_script.substitute('{job_result_key}', 'None')
            srun_py_script.substitute('{job_index_file}', job_index_file)
            srun_py_script.write()

            if srun_opts is not 'fake':
                srun_sh_script = ShellScript("""
                    #!/bin/bash
                    set -e

                    srun {srun_opts} {srun_py_script}
                """, keep_temp_files=keep_temp_files)
            else:
                srun_sh_script = ShellScript("""
                    #!/bin/bash
                    set -e

                    {srun_py_script}
                """, keep_temp_files=keep_temp_files)
            srun_sh_script.substitute('{srun_opts}', srun_opts)
            srun_sh_script.substitute('{srun_py_script}', srun_py_script.scriptPath())
            srun_sh_script.start()
            while srun_sh_script.isRunning():
                srun_sh_script.wait(5)
            if srun_sh_script.returnCode() != 0:
                raise Exception('Non-zero return code for srun script.')
            result_objects=[]
            for ii, job in enumerate(jobs):
                result_object = local_client.loadObject(key=job_result_key, subkey=str(ii))
                if result_object is None:
                    raise Exception('Unexpected problem in executeBatch (srun mode): result object is none')
                result_objects.append(result_object)
            results = [MountainJobResult(result_object=obj) for obj in result_objects]
    
    return results

def _take_next_batch_job_index_to_run(job_index_file):
    while True:
        time.sleep(random.uniform(0, 0.1))
        fname2=_attempt_lock_file(job_index_file)
        if fname2:
            index=int(_read_text_file(fname2))
            _write_text_file(fname2,'{}'.format(index+1))
            os.rename(fname2,job_index_file) # put it back
            return index

def _attempt_lock_file(fname):
    if os.path.exists(fname):
        fname2=fname+'.lock.'+_random_string(6)
        try:
            os.rename(fname, fname2)
        except:
            return False
        if os.path.exists(fname2):
            return fname2

def _set_job_status(job, status):
    local_client = MountainClient()
    job_status_key = getattr(job, 'job_status_key', None)
    job_index = getattr(job, 'job_index', None)
    if job_status_key:
        subkey = str(job_index)
        local_client.setValue(key=job_status_key, subkey=subkey, value=status)

def _set_job_result(job, result_object):
    local_client = MountainClient()
    job_result_key = getattr(job, 'job_result_key', None)
    job_index = getattr(job, 'job_index', None)
    if job_result_key:
        subkey = str(job_index)
        local_client.saveObject(key=job_result_key, subkey=subkey, object=result_object)

def _execute_job(job):
    local_client = MountainClient()
    halt_key = getattr(job, 'halt_key', None)
    if halt_key:
        halt_val = local_client.getValue(key=halt_key)
        if halt_val:
            raise Exception('Batch halted.')
    
    _set_job_status(job, 'running')

    result = job.execute()

    if result.retcode == 0:
        _set_job_status(job, 'finished')
    else:
        _set_job_status(job, 'error')

    _set_job_result(job, result.getObject())

    return result

def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))

def _write_text_file(fname,txt):
    with open(fname,'w') as f:
        f.write(txt)

def _read_text_file(fname):
    with open(fname,'r') as f:
        return f.read()
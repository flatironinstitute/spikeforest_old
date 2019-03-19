import os
import multiprocessing
from mountainclient import client as mt
from mountainclient import MountainClient
from .computeresourceclient import ComputeResourceClient

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

def executeBatch(*, jobs, label='', num_workers=None, compute_resource=None, batch_name=None, halt_key=None, job_status_key=None):
    if len(jobs) == 0:
        return []

    if num_workers is not None:
        if compute_resource is not None:
            raise Exception('Cannot specify both num_workers and compute_resource in executeBatch.')

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

    for job_index, job in enumerate(jobs):
        setattr(job, 'halt_key', halt_key)
        setattr(job, 'job_status_key', job_status_key)
        setattr(job, 'job_index', job_index)

    if num_workers is not None:
        pool = multiprocessing.Pool(num_workers)
        results = pool.map(_execute_job, jobs)
        pool.close()
        pool.join()
    else:
        results = []
        for job in jobs:
            results.append(_execute_job(job))
    for i, job in enumerate(jobs):
        job.result = results[i]
    
    return results

def _set_job_status(job, status):
    job_status_key = getattr(job, 'job_status_key', None)
    job_index = getattr(job, 'job_index', None)
    if job_status_key:
        subkey = str(job_index)
        mt.setValue(key=job_status_key, subkey=subkey, value=status)

def _execute_job(job):
    halt_key = getattr(job, 'halt_key', None)
    if halt_key:
        halt_val = mt.getValue(key=halt_key)
        if halt_val:
            raise Exception('Batch halted.')
    
    _set_job_status(job, 'running')

    result = job.execute()

    if result.retcode == 0:
        _set_job_status(job, 'finished')
    else:
        _set_job_status(job, 'error')

    return result

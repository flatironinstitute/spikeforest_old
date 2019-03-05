#!/usr/bin/env python

import asyncio
import os
import sys
import argparse
import time
import mlprocessors as mlpr
import traceback
from cairio import CairioClient
from mlprocessors import _prepare_processor_job, executeJob
import asyncio
import random
import time

# This can be important for some of the jobs in certain situations
os.environ['DISPLAY'] = ''

def run_batch_job(collection,share_id,token,upload_token,batch_id,job_index, system_call=False, srun_opts_string=None):
    cairio_client=CairioClient()
    if collection:
        cairio_client.configRemoteReadWrite(collection=collection,share_id=share_id,token=token,upload_token=upload_token)
    else:
        cairio_client.configLocal()

    # check if batch is halted
    _check_batch_halt(cairio_client, batch_id)

    if system_call:
        scriptpath = os.path.realpath(__file__)
        opts=[]
        if collection:
            opts.append('--collection '+collection)
        if share_id:
            opts.append('--share_id '+share_id)
        if token:
            opts.append('--token '+token)
        if upload_token:
            opts.append('--upload_token '+upload_token)
        opts.append('--batch_id '+batch_id)
        if job_index is not None:
            opts.append('--job_index {}'.format(job_index))
        cmd=scriptpath+' '+' '.join(opts)
        if srun_opts_string is not None:
            _init_next_batch_job_index_to_run(cairio_client=cairio_client, batch_id=batch_id)
            cmd = 'srun {} {}'.format(srun_opts_string, cmd)
        # be careful about printing this command... it may contain the secrets
        print('##################### {}'.format(cmd))
        retval = os.system(cmd)
        if retval != 0:
            raise Exception('Error running batch job {} (batch_id={})'.format(job_index, batch_id))
        return

    if srun_opts_string is not None:
        raise Exception('Cannot use srun without system_call.')

    batch=cairio_client.loadObject(
        key=dict(
            name='compute_resource_batch',
            batch_id=batch_id
        )
    )
    if batch is None:
        raise Exception('Unable to load batch object (batch_id={})'.format(batch_id))
    jobs=batch['jobs']

    def do_run_job(index):
        print('Running job {} of {}'.format(index, len(jobs)))
        job=jobs[index]
        result=executeJob(job, cairio_client=cairio_client)
        cairio_client.saveObject(
            key=dict(
                name='compute_resource_batch_job_result',
                batch_id=batch_id,
                job_index=job_index
            ),
            object=result
        )

    if job_index is not None:
        do_run_job(job_index)
    else:
        while True:
            index=_take_next_batch_job_index_to_run(cairio_client=cairio_client, batch_id=batch_id)
            if (index is not None) and (index<len(jobs)):
                do_run_job(index)
            else:
                break

def _init_next_batch_job_index_to_run(*, cairio_client, batch_id):
    key = dict(name='compute_resource_next_batch_job_index_to_run',
               batch_id=batch_id)
    cairio_client.setValue(key=key, value=str(0))

def _take_next_batch_job_index_to_run(*, cairio_client, batch_id):
    key = dict(name='compute_resource_next_batch_job_index_to_run',
               batch_id=batch_id)
    last_attempted_job_index = -1
    last_attempted_job_index_timestamp = time.time()
    while True:
        val = cairio_client.getValue(key=key)
        if val is None:
            return None
        job_index = int(val)
        if _acquire_job_lock(cairio_client=cairio_client, batch_id=batch_id, job_index=job_index):
            cairio_client.setValue(key=key, value=str(job_index+1))
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

def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))

def _acquire_job_lock(*, cairio_client, batch_id, job_index):
    key = dict(name='compute_resource_job_lock',
               batch_id=batch_id)
    code = 'lock_'+_random_string(10)
    return cairio_client.setValue(key=key, subkey=str(job_index), value=code, overwrite=False)

def _check_batch_halt(cairio_client,batch_id):
    key=dict(
        name='compute_resource_batch_halt',
        batch_id=batch_id
    )
    val=cairio_client.getValue(key=key)
    if val is not None:
        print('BATCH HALTED (batch_id={})'.format(batch_id))
        raise Exception('Stopping batch (batch_id={})'.format(batch_id))

def main():
    parser = argparse.ArgumentParser(
        description='Run a processing batch')
    parser.add_argument('--collection', help='Collection to connect to', required=False, default=None)
    parser.add_argument('--share_id', help='KBucket share to connect to', required=False, default=None)
    parser.add_argument('--token', help='token for collection', required=False, default=None)
    parser.add_argument('--upload_token', help='secret for uploading to kbucket', required=False, default=None)
    parser.add_argument('--batch_id', help='ID of the batch to run', required=True)
    parser.add_argument('--job_index', help='index of the job to run. If None, will run all jobs -- compatible with srun.', required=False, default=None)

    args = parser.parse_args()

    job_index=args.job_index
    if job_index is not None:
        job_index = int(job_index)

    try:
        run_batch_job(collection=args.collection, share_id=args.share_id, token=args.token, upload_token=args.upload_token, batch_id=args.batch_id, job_index=job_index)
    except Exception as err:
        traceback.print_exc()
        print('Error running batch job:', err)
        sys.exit(-1)


if __name__ == "__main__":
    main()

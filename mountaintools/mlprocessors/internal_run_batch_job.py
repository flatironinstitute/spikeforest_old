#!/usr/bin/env python

import asyncio
import os
import sys
import argparse
import time
import mlprocessors as mlpr
import traceback
from mountaintools import CairioClient
import asyncio
import random
import time

def run_batch_job(collection, share_id, batch_id, job_index, system_call=False, srun_opts_string=None):
    local_client=CairioClient()

    # check if batch is halted
    _check_batch_halt(local_client, batch_id)

    if system_call:
        scriptpath = os.path.realpath(__file__)
        opts=[]
        if collection:
            opts.append('--collection '+collection)
        if share_id:
            opts.append('--share_id '+share_id)
        opts.append('--batch_id '+batch_id)
        if job_index is not None:
            opts.append('--job_index {}'.format(job_index))
        cmd=scriptpath+' '+' '.join(opts)
        if srun_opts_string is not None:
            _init_next_batch_job_index_to_run(batch_id=batch_id)
            cmd = 'srun {} {}'.format(srun_opts_string, cmd)
        retval = os.system(cmd)
        if retval != 0:
            raise Exception('Error running batch job {} (batch_id={})'.format(job_index, batch_id))
        return

    if srun_opts_string is not None:
        raise Exception('Cannot use srun without system_call.')

    batch=local_client.loadObject(
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
        _check_batch_halt(local_client, batch_id)
        _set_batch_job_status(cairio_client=local_client, batch_id=batch_id, job_index=index, status='running')
        job=jobs[index]
        result=executeJob(job, cairio_client=local_client)
        key=dict(
            name='compute_resource_batch_job_result',
            batch_id=batch_id,
            job_index=index
        )
        local_client.saveObject(
            key=key,
            object=result
        )
        if result.get('retcode', 0) ==0:
            _set_batch_job_status(cairio_client=local_client, batch_id=batch_id, job_index=index, status='finished')
        else:
            _set_batch_job_status(cairio_client=local_client, batch_id=batch_id, job_index=index, status='error')

    if job_index is not None:
        do_run_job(job_index)
    else:
        while True:
            index=_take_next_batch_job_index_to_run(batch_id=batch_id)
            if (index is not None) and (index<len(jobs)):
                do_run_job(index)
            else:
                break

def _write_text_file(fname,txt):
    with open(fname,'w') as f:
        f.write(txt)

def _read_text_file(fname):
    with open(fname,'r') as f:
        return f.read()

def _attempt_lock_file(fname):
    if os.path.exists(fname):
        fname2=fname+'.lock.'+_random_string(6)
        try:
            os.rename(fname, fname2)
        except:
            return False
        if os.path.exists(fname2):
            return fname2

def _init_next_batch_job_index_to_run(*, batch_id):
    fname='job_index--'+batch_id+'.txt'
    _write_text_file(fname, '0')

def _take_next_batch_job_index_to_run(*, batch_id):
    fname='job_index--'+batch_id+'.txt'
    while True:
        time.sleep(random.uniform(0, 0.2))
        fname2=_attempt_lock_file(fname)
        if fname2:
            index=int(_read_text_file(fname2))
            _write_text_file(fname2,'{}'.format(index+1))
            os.rename(fname2,fname)
            return index

def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))

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
    parser.add_argument('--batch_id', help='ID of the batch to run', required=True)
    parser.add_argument('--job_index', help='index of the job to run. If None, will run all jobs -- compatible with srun.', required=False, default=None)

    args = parser.parse_args()

    job_index=args.job_index
    if job_index is not None:
        job_index = int(job_index)

    try:
        run_batch_job(collection=args.collection, share_id=args.share_id, batch_id=args.batch_id, job_index=job_index)
    except Exception as err:
        traceback.print_exc()
        print('Error running batch job:', err)
        sys.exit(-1)

def _set_batch_job_status(*, cairio_client, batch_id, job_index, status):
    key=dict(
        name='compute_resource_batch_job_statuses',
        batch_id=batch_id
    )
    cairio_client.setValue(key=key,subkey=str(job_index),value=status)

if __name__ == "__main__":
    main()

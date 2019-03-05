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

# This can be important for some of the jobs in certain situations
os.environ['DISPLAY'] = ''

def run_batch_job(collection,share_id,token,upload_token,batch_id,job_index, system_call=False, srun_opts_string=None, num_jobs=None):
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
            if srun_opts_string:
                raise Exception('Cannot use job_index with srun_opts_string')
            opts.append('--job_index {}'.format(job_index))
            opts.append('-n {}'.format(num_jobs))
        cmd=scriptpath+' '+' '.join(opts)
        if srun_opts_string:
            cmd='srun {} bash -c "{} --job_index \$SLURM_PROCID"'.format(srun_opts_string, cmd)
        # be careful about printing this command... it may contain the secrets
        print('##################### {}'.format(cmd))
        retval = os.system(cmd)
        if retval != 0:
            raise Exception('Error running batch job {} (batch_id={})'.format(job_index, batch_id))
        return

    if srun_opts_string:
        raise Exception('Cannot use srun opts string with system_call==False')

    batch=cairio_client.loadObject(
        key=dict(
            name='compute_resource_batch',
            batch_id=batch_id
        )
    )
    if batch is None:
        raise Exception('Unable to load batch object (batch_id={})'.format(batch_id))
    jobs=batch['jobs']
    job=jobs[job_index]

    result=executeJob(job, cairio_client=cairio_client)

    cairio_client.saveObject(
        key=dict(
            name='compute_resource_batch_job_result',
            job_index=job_index
        ),
        object=result
    )

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
    parser.add_argument('--job_index', help='index of the job to run', required=True)

    args = parser.parse_args()

    try:
        run_batch_job(collection=args.collection, share_id=args.share_id, token=args.token, upload_token=args.upload_token, batch_id=args.batch_id,job_index=int(args.job_index))
    except Exception as err:
        traceback.print_exc()
        print('Error running batch job:', err)
        sys.exit(-1)


if __name__ == "__main__":
    main()
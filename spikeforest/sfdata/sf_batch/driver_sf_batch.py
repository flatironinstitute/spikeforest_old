#!/usr/bin/env python

import argparse
import spikeforest as sf
from cairio import client as ca
import os
import json

def read_json_file(fname):
    with open(fname) as f:
        return json.load(f)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Run SpikeForest batch processing')
    parser.add_argument('command',help='clear, prepare, run, assemble')
    parser.add_argument('batch_name',help='Name of the batch')
    args = parser.parse_args()

    batch_name=args.batch_name

    spikeforest_password=os.environ.get('SPIKEFOREST_PASSWORD','')
    if not spikeforest_password:
      raise Exception('Environment variable not set: SPIKEFOREST_PASSWORD')
    
    print('Loading batch: '+batch_name)
    sf.kbucketConfigRemote(name='spikeforest1-readwrite',password=spikeforest_password)
    obj=ca.loadObject(key=dict(batch_name=batch_name))
    if not obj:
      raise Exception('Unable to find batches object.')

    command=args.command
    if command=='clear':
      sf.sf_batch.clear_job_results(batch_name=batch_name,incomplete_only=False)
    elif command=='prepare':
      sf.sf_batch.download_recordings(batch_name=batch_name)
      sf.sf_batch.clear_job_results(batch_name=batch_name,incomplete_only=True)
    elif command=='run':
      sf.sf_batch.run_jobs(batch_name=batch_name)
    elif command=='assemble':
      sf.sf_batch.assemble_job_results(batch_name=batch_name)
    else:
      raise Exception('Unrecognized command: '+command)

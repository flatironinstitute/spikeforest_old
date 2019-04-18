#!/usr/bin/env python

import os
import sys
import subprocess
import random
import multiprocessing
import mlprocessors as mlpr
from mlprocessors import ShellScript
import mtlogging
import signal

def main():
    with LocalComputeResource(num_parallel=1) as compute_resource:
        print(compute_resource)
        S = ShellScript("""
            #!/bin/bash
            set -e
            ./main_analysis.py --recording_group toy_recordings --output_id toy_recordings --compute_resource_default {resource_name} --compute_resource_gpu {resource_name} --sorter_codes=ms4,sc,yass
        """)
        S.substitute('{resource_name}', compute_resource['resource_name'])

        S.start()
        S.wait()

class LocalComputeResource():
    def __init__(self,num_parallel):
        self._num_parallel=num_parallel
        self._exit_event = multiprocessing.Event()
    def __enter__(self):
        from mountaintools import client as mt
        resource_name='local_resource_'+_random_string(6)
        self._process=multiprocessing.Process(target=_run_local_compute_resource, args=(resource_name,self._num_parallel, self._exit_event))
        self._process.start()
        
        return dict(resource_name=resource_name,collection=None,share_id=None)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit_event.set()
        print('Stopping local compute resource')
        self._process.join(5)
        print('.')
        self._process.terminate()

@mtlogging.log(root=True)
def _run_local_compute_resource(resource_name, num_parallel, exit_event):
    import mlprocessors as mlpr
    from mountaintools import client as mt
    server=mlpr.ComputeResourceServer(
        resource_name=resource_name,
        collection=None,
        share_id=None
    )
    server.setNumParallel(num_parallel)
    server.start(exit_event=exit_event)


def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))


if __name__ == '__main__':
    main()
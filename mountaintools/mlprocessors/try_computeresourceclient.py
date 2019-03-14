#!/usr/bin/env python

import asyncio
from computeresourceclient import ComputeResourceClient
from nthprime import ComputeNthPrime
from mountaintools import client as ca
import mlprocessors as mlpr

def main():
    ca.login()
    compute_resource=dict(
        #resource_name='crtest1',
        resource_name='ccmlin008-default',
        collection='spikeforest',
        share_id='spikeforest.spikeforest2'
    )

    # compute_resource=dict(resource_name='test_resource')

    jobs=[]
    for n in range(50100,50200,10):
        jobs.append(
            ComputeNthPrime.createJob(
                n=n,
                output='test_output/test_{}.txt'.format(n),
                _force_run=False
            )
        )

    mlpr.executeBatch(jobs=jobs, compute_resource=compute_resource)
    

if __name__ == "__main__":
    main()
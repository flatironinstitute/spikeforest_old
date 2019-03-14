#!/usr/bin/env python

import asyncio
from mountaintools import client as ca
from computeresourceserver import ComputeResourceServer

def main():
    ca.login()
    server=ComputeResourceServer(
        resource_name='crtest1',
        collection='spikeforest',
        share_id='69432e9201d0'
    )

    # server=ComputeResourceServer(resource_name='crtest_local')

    server.setMaxSimultaneousJobs(10)
    server.start()

if __name__ == "__main__":
    main()
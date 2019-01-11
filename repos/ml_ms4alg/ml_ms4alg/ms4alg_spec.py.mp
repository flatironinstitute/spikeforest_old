#!/usr/bin/env python3

import sys

from mountainlab_pytools import processormanager as pm

import p_ms4alg

PM=pm.ProcessorManager()

PM.registerProcessor(p_ms4alg.sort)

if not PM.run(sys.argv):
    exit(-1)

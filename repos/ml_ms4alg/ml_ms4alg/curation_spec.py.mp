#!/usr/bin/env python3

import sys

from mountainlab_pytools import processormanager as pm

import p_create_label_map
import p_apply_label_map

PM=pm.ProcessorManager()

PM.registerProcessor(p_create_label_map.create_label_map)
PM.registerProcessor(p_apply_label_map.apply_label_map)

if not PM.run(sys.argv):
    exit(-1)

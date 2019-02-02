#!/bin/bash
set -ex

# you must first pip install autopep8
autopep8 -ir batcho kbucket mlprocessors pages pairio spikesorters vdomr

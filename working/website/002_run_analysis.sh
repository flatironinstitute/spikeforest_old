#!/bin/bash
set -e

COMPUTE_RESOURCE=${1:-ccmlin008}
JOB_TIMEOUT_SEC=${2:-1200}

cd ../main_analysis
./run_all.sh $COMPUTE_RESOURCE $JOB_TIMEOUT_SEC
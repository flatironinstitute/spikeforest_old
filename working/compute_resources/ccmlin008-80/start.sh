#!/bin/bash
set -e

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

export DISPLAY=""

# Use the following to connect to spikeforest2
export CAIRIO_CONFIG=spikeforest.spikeforest2-readwrite
export CAIRIO_CONFIG_PASSWORD=$SPIKEFOREST_PASSWORD

# find containers (look in spikeforest2)
export CAIRIO_ALTERNATE_SHARE_IDS=69432e9201d0

../../../bin/batcho_listen ccmlin008-80 --allow_uncontainerized --run_prefix="srun -c 2 -n 80 -p ccm" 2>&1 | tee output.txt

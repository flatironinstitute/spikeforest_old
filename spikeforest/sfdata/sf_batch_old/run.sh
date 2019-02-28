#!/bin/bash

set -e

# Set number of cpu's to use for spike sorting
export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

batch_name=$1

python driver_sf_batch.py prepare $batch_name
python driver_sf_batch.py run $batch_name
# srun -c 2 -n 80 -p ccb --qos=ccb python driver_sf_batch.py run $batch_name
python driver_sf_batch.py assemble $batch_name

#!/bin/bash

BATCH_NAME=$1
DIR=`dirname "$0"`

export NUM_WORKERS=1
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

singularity exec \
  --contain -B $KBUCKET_CACHE_DIR:$KBUCKET_CACHE_DIR \
  -B $PWD:/spikeforest_batch_run -B /tmp:/tmp \
  $DIR/../../sf_spyking_circus/sf_spyking_circus.simg bash \
  -c "cd /spikeforest_batch_run && PYTHONPATH=/spikeforest_batch_run /spikeforest_batch_run/bin/sf_run_batch_command run $BATCH_NAME"


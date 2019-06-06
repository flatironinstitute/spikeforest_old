#!/bin/bash
set -e

RESOURCE_NAME=${1:-ccmlin008-80}
SRUN_TIMEOUT_MIN=${2:-120}

export MLPROCESSORS_FORCE_RUN=FALSE
export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

export DISPLAY=""
COLLECTION=spikeforest
KACHERY_NAME=kbucket

compute-resource-start $RESOURCE_NAME \
	--allow_uncontainerized  \
	--collection $COLLECTION --kachery_name $KACHERY_NAME \
        --srun_opts "-c 2 -n 60 -p gen --time $SRUN_TIMEOUT_MIN"


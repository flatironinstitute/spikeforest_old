#!/bin/bash
set -e

module load matlab

MLPROCESSORS_FORCE_RUN=FALSE

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

export DISPLAY=""
RESOURCE_NAME=${1:-ccmlin008-sc}
COLLECTION=spikeforest
KACHERY_NAME=kbucket

../../../bin/compute-resource-start $RESOURCE_NAME \
	--allow_uncontainerized  \
	--collection $COLLECTION --kachery_name $KACHERY_NAME \
        --srun_opts "-c 12 -n 10 -p ccm"



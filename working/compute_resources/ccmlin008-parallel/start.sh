#!/bin/bash
set -e

MLPROCESSORS_FORCE_RUN=FALSE

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

export DISPLAY=""
RESOURCE_NAME=${1:-ccmlin008-parallel} 
NUM_THREADS=${2:-10} 

COLLECTION=spikeforest
SHARE_ID=69432e9201d0

#../../../bin/compute-resource-start ccmlin000-80 \
#	--allow_uncontainerized  \
#	--collection $COLLECTION --share_id $SHARE_ID \
#        --srun_opts "-c 2 -n 80 -p ccm"

../../../bin/compute-resource-start $RESOURCE_NAME \
	--allow_uncontainerized  \
	--collection $COLLECTION --share_id $SHARE_ID \
        --parallel $NUM_THREADS
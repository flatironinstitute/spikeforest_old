#!/bin/bash
set -e

# default name otherwise specified
RESOURCE_NAME=${1:-ccmlin008-gpu} 

module load matlab
module load cuda

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

export DISPLAY=""

COLLECTION=spikeforest
SHARE_ID=69432e9201d0

#../../../bin/compute-resource-start $RESOURCE_NAME \
#	--allow_uncontainerized --parallel 1  \
#	--collection $COLLECTION --share_id $SHARE_ID

../../../bin/compute-resource-start $RESOURCE_NAME \
	--allow_uncontainerized  \
	--collection $COLLECTION --share_id $SHARE_ID \
        --srun_opts "-n 6 -c 2 -p gpu --gres=gpu:1 --constraint=v100" \
        --parallel 4

#../../../bin/compute-resource-start $RESOURCE_NAME \
#	--allow_uncontainerized  \
#	--collection $COLLECTION --share_id $SHARE_ID \
#        --srun_opts "-n 1 -c 8 -p gpu --gres=gpu:1 --constraint=v100" \
#        --parallel 6

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
KACHERY_NAME=kbucket

#compute-resource-start $RESOURCE_NAME \
#	--allow_uncontainerized --parallel 1  \
#	--collection $COLLECTION --kachery_name $KACHERY_NAME

compute-resource-start $RESOURCE_NAME \
	--allow_uncontainerized  \
	--collection $COLLECTION --kachery_name $KACHERY_NAME \
        --srun_opts "-n 4 -c 2 -p gpu --gres=gpu:1 --constraint=v100 --time 120" \
        --parallel 2

#compute-resource-start $RESOURCE_NAME \
#	--allow_uncontainerized  \
#	--collection $COLLECTION --kachery_name $KACHERY_NAME \
#        --parallel 2

#compute-resource-start $RESOURCE_NAME \
#	--allow_uncontainerized  \
#	--collection $COLLECTION --kachery_name $KACHERY_NAME \
#        --srun_opts "-n 1 -c 2 -p gpu --gres=gpu:1" \
#        --parallel 1



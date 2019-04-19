#!/bin/bash
set -e

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

export DISPLAY=""

COLLECTION=spikeforest
KACHERY_NAME=kbucket

../../../bin/compute-resource-start ccmlin008-default \
	--allow_uncontainerized --parallel 10  \
	--collection $COLLECTION --kachery_name $KACHERY_NAME


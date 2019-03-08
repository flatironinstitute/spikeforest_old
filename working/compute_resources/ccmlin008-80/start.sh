#!/bin/bash
set -e

MLPROCESSORS_FORCE_RUN=TRUE

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

export DISPLAY=""

COLLECTION=spikeforest
SHARE_ID=69432e9201d0

../../../bin/compute-resource-start ccmlin008-80 \
	--allow_uncontainerized  \
	--collection $COLLECTION --share_id $SHARE_ID \
        --srun_opts "-c 2 -n 80 -p ccm"


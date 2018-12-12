#!/bin/bash

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

OPTS="--run_prefix \"srun -c 2 -n 40\""
#OPTS=""

#eval "bin/sf_run_batch ms4_magland_synth $OPTS"

#eval "bin/sf_run_batch ms4_bionet8c $OPTS"

eval "bin/sf_run_batch ms4_bionet32c $OPTS"

eval "bin/sf_run_batch ms4_mearec_tetrode $OPTS"

eval "bin/sf_run_batch ms4_mearec_neuronexus $OPTS"


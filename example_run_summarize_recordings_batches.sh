#!/bin/bash

OPTS="--run_prefix \"srun -c 2 -n 40 -p ccm --time=03:00:00\""
#OPTS="--clear"
#OPTS=""
#OPTS=""

export DISPLAY=

#eval "bin/sf_run_batch summarize_recordings_bionet8c $OPTS"
eval "bin/sf_run_batch summarize_recordings_bionet32c $OPTS"
eval "bin/sf_run_batch summarize_recordings_magland_synth $OPTS"
eval "bin/sf_run_batch summarize_recordings_mearec_tetrode $OPTS"
eval "bin/sf_run_batch summarize_recordings_mearec_neuronexus $OPTS"


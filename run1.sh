#!/bin/bash

#OPTS="--run_prefix \"srun -c 2 -n 40 -p ccm --time=01:00:00\""
#OPTS="--clear --job_index 0 --mlpr_force_run"
OPTS="--clear --job_index 0"
#OPTS=""
#OPTS="--parallel 10"

export DISPLAY=

export NUM_WORKERS=1
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

#eval "bin/sf_run_batch ms4_bionet8c $OPTS"
#eval "bin/sf_run_batch ms4_bionet32c $OPTS"
eval "bin/sf_run_batch ms4_magland_synth $OPTS"
#eval "bin/sf_run_batch ms4_mearec_tetrode $OPTS"
#eval "bin/sf_run_batch ms4_mearec_neuronexus $OPTS"

#eval "bin/sf_run_batch sc_bionet8c $OPTS"
#eval "bin/sf_run_batch sc_bionet32c $OPTS"
#eval "bin/sf_run_batch sc_magland_synth $OPTS"
#eval "bin/sf_run_batch sc_mearec_tetrode $OPTS"
#eval "bin/sf_run_batch sc_mearec_neuronexus $OPTS"

#eval "bin/sf_run_batch irc_bionet8c $OPTS"
#eval "bin/sf_run_batch irc_bionet32c $OPTS"
#eval "bin/sf_run_batch irc_magland_synth $OPTS"
#eval "bin/sf_run_batch irc_mearec_tetrode $OPTS"
#eval "bin/sf_run_batch irc_mearec_neuronexus $OPTS"

#eval "bin/sf_run_batch ks_bionet8c $OPTS"
#eval "bin/sf_run_batch ks_bionet32c $OPTS"
#eval "bin/sf_run_batch ks_magland_synth $OPTS"
#eval "bin/sf_run_batch ks_mearec_tetrode $OPTS"
#eval "bin/sf_run_batch ks_mearec_neuronexus $OPTS"



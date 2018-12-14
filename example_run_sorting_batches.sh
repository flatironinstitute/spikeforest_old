#!/bin/bash

#OPTS="--run_prefix \"srun -c 2 -n 40 -p ccm --time=01:00:00\""
#OPTS="--clear"
#OPTS=""
OPTS="--parallel 10"

export DISPLAY=

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

#eval "bin/sf_run_batch2 ms4_bionet8c $OPTS"
#eval "bin/sf_run_batch2 ms4_bionet32c $OPTS"
#eval "bin/sf_run_batch2 ms4_magland_synth $OPTS"
#eval "bin/sf_run_batch2 ms4_mearec_tetrode $OPTS"
#eval "bin/sf_run_batch2 ms4_mearec_neuronexus $OPTS"

#eval "bin/sf_run_batch2 sc_bionet8c $OPTS"
#eval "bin/sf_run_batch2 sc_bionet32c $OPTS"
#eval "bin/sf_run_batch2 sc_magland_synth $OPTS"
#eval "bin/sf_run_batch2 sc_mearec_tetrode $OPTS"
#eval "bin/sf_run_batch2 sc_mearec_neuronexus $OPTS"

#eval "bin/sf_run_batch2 irc_bionet8c $OPTS"
#eval "bin/sf_run_batch2 irc_bionet32c $OPTS"
#eval "bin/sf_run_batch2 irc_magland_synth $OPTS"
#eval "bin/sf_run_batch2 irc_mearec_tetrode $OPTS"
#eval "bin/sf_run_batch2 irc_mearec_neuronexus $OPTS"

#eval "bin/sf_run_batch2 ks_bionet8c $OPTS"
#eval "bin/sf_run_batch2 ks_bionet32c $OPTS"
eval "bin/sf_run_batch2 ks_magland_synth $OPTS"
#eval "bin/sf_run_batch2 ks_mearec_tetrode $OPTS"
#eval "bin/sf_run_batch2 ks_mearec_neuronexus $OPTS"



!/bin/bash
set -ex


module load slurm matlab singularity cuda/9.1.85
STUDY=$1  # name of the study, e.g. crcns

OPTS_GPU="--run_prefix \"srun -c 2 -n 20 --gres=gpu:2 -p gpu\""
OPTS="--run_prefix \"srun -c 2 -n 40 -p ccm\""
OPTS_CLEAR="--clear"
OPTS_NONE=""
OPTS_LOCAL="--parallel 10"
OPTS_DEBUG="--mlpr_keep_temp_files"

export DISPLAY=

export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

# summarize recording batch
eval "bin/sf_run_batch summarize_recordings_$STUDY $OPTS_CLEAR"

# run sorting batches
eval "bin/sf_run_batch ms4_$STUDY $OPTS        #--clear"  #eval "bin/sf_run_batch ms4_$STUDY $OPTS"
eval "bin/sf_run_batch irc_$STUDY $OPTS_GPU"
eval "bin/sf_run_batch sc_$STUDY $OPTS"
eval "bin/sf_run_batch ks_$STUDY $OPTS_NONE"

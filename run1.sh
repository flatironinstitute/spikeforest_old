#!/bin/bash

#bin/sf_run_batch summarize_recordings_bionet8c --run_prefix "srun -c 2 -n 40"
#bin/sf_run_batch summarize_recordings_bionet32c --run_prefix "srun -c 2 -n 40"
#bin/sf_run_batch summarize_recordings_magland_synth --run_prefix "srun -c 2 -n 40"
#bin/sf_run_batch summarize_recordings_mearec_tetrode --run_prefix "srun -c 2 -n 40"
bin/sf_run_batch summarize_recordings_mearec_neuronexus --run_prefix "srun -c 2 -n 40"


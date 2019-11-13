#!/bin/bash
set -e

./prepare_hybrid_janelia_recordings.py
./prepare_manual_franklab_recordings.py
# ./prepare_synth_monotrode_recordings.py
./prepare_paired_recordings.py
./prepare_paired_monotrode_recordings.py
./prepare_synth_bionet_recordings.py
./prepare_synth_magland_recordings.py
./prepare_synth_mearec_neuronexus_recordings.py
# ./prepare_synth_mearec_sqmea64c_recordings.py
./prepare_synth_mearec_tetrode_recordings.py
./prepare_synth_visapy_recordings.py
./prepare_synth_monotrode_recordings.py

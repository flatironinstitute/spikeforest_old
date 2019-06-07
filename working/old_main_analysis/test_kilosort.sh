#!/bin/bash
set -e

# You should make local versions of this script and then change the settings and
# comment out lines as needed

RESOURCE_CPU=${1:-ccmlin008-80}
RESOURCE_GPU=${2:-ccmlin008-gpu}

OPTS=""
OPTS="$OPTS --compute_resource_default $RESOURCE_CPU --compute_resource_gpu $RESOURCE_GPU"
OPTS="$OPTS --collection spikeforest --share_id spikeforest.spikeforest2"
OPTS="$OPTS --sorter_codes ks"

SUFFIX="_ks"

./main_analysis.py --recording_group magland_synth --output_id magland_synth$SUFFIX $OPTS "${@:3}"
./main_analysis.py --recording_group visapy_mea --output_id visapy_mea$SUFFIX $OPTS "${@:3}"
./main_analysis.py --recording_group paired --output_id paired$SUFFIX $OPTS "${@:3}"
./main_analysis.py --recording_group manual_tetrode --output_id manual_tetrode$SUFFIX $OPTS "${@:3}"
./main_analysis.py --recording_group mearec_neuronexus --output_id mearec_neuronexus$SUFFIX $OPTS "${@:3}"
#./main_analysis.py --recording_group mearec_sqmea --output_id mearec_sqmea$SUFFIX $OPTS "${@:3}"
./main_analysis.py --recording_group mearec_tetrode --output_id mearec_tetrode$SUFFIX $OPTS "${@:3}"
./main_analysis.py --recording_group bionet --output_id bionet$SUFFIX $OPTS "${@:3}"


#!/bin/bash
set -e

#declare -a list=("test_reliability" "test_samplerate")
declare -a list=("paired_monotrode" "synth_monotrode")

OPTS="--compute_resources compute_resources_ccmlin000.json"

for item in "${list[@]}"
do 
    echo "=============================================================================" | tee all.${item}.0.log
    echo "$(date): Processing ${item} -- see all.${item}.0.log" | tee -a all.${item}.0.log
    echo "=============================================================================" | tee -a all.${item}.0.log
    ./spikeforest_analysis analysis.${item}.json $OPTS >> all.${item}.0.log
    cat all.${item}.0.log >> all.${item}.log
    cat all.${item}.0.log >> all.processing.log
    echo ""

done


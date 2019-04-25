#!/bin/bash
set -e

declare -a list=("visapy_synth" "magland_synth" "mearec_tetrode" "manual_tetrode")

while true
do
    for item in "${list[@]}"
    do 
        echo "=============================================================================" | tee ${item}.0.log
        echo "$(date): Processing ${item} -- see ${item}.0.log" | tee -a ${item}.0.log
        echo "=============================================================================" | tee -a ${item}.0.log
        ./spikeforest_analysis analysis.${item}.json >> ${item}.0.log
        cat ${item}.0.log >> ${item}.log
        cat ${item}.0.log >> continuous.processing.log
        echo ""

    done
    echo "Sleeping..."
    sleep 60
done

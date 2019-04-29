#!/bin/bash
set -e

declare -a list=("paired_boyden32c" "paired_crcns" "paired_neuropix32c" "paired_mea64c" "synth_visapy" "synth_magland" "synth_mearec_tetrode" "manual_franklab" "synth_bionet" "synth_mearec_neuronexus")

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
    sleep 600
done

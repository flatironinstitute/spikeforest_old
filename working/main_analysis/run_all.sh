#!/bin/bash
set -e

declare -a list=("paired_boyden32c" "paired_crcns" "paired_kampff" "paired_mea64c" "synth_visapy" "synth_magland" "synth_mearec_tetrode" "manual_franklab" "synth_bionet" "synth_mearec_neuronexus")

for item in "${list[@]}"
do 
    echo "=============================================================================" | tee all.${item}.0.log
    echo "$(date): Processing ${item} -- see all.${item}.0.log" | tee -a all.${item}.0.log
    echo "=============================================================================" | tee -a all.${item}.0.log
    ./spikeforest_analysis analysis.${item}.json >> all.${item}.0.log
    cat all.${item}.0.log >> all.${item}.log
    cat all.${item}.0.log >> all.processing.log
    echo ""

done


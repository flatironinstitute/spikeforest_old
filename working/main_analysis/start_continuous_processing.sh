#!/bin/bash

declare -a list=("visapy_synth" "magland_synth" "mearec_tetrode", "manual_tetrode")

while true
do
    for item in "${list[@]}"
    do 
        echo "============================================================================="
        echo "== ${item}"
        echo "============================================================================="
        ./spikeforest_analysis analysis.${item}.json > ${item}.0.log
        cat ${item}.0.log >> ${item}.log
        echo ""
        echo ""
        echo ""

    done
    echo "Sleeping..."
    sleep 60
done

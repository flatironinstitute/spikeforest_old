#!/bin/bash

RESOURCE_CPU=${1:-ccmlin000-80}
RESOURCE_GPU=${2:-ccmlin000-parallel}

#./process_magland_synth_test.py 
./process_bionet.py $RESOURCE_CPU $RESOURCE_GPU
./process_magland_synth.py $RESOURCE_CPU $RESOURCE_GPU
./process_visapy_mea.py $RESOURCE_CPU $RESOURCE_GPU 

./process_paired.py $RESOURCE_CPU $RESOURCE_GPU 
./process_manual_tetrode.py $RESOURCE_CPU $RESOURCE_GPU 
./process_mearec_neuronexus.py $RESOURCE_CPU $RESOURCE_GPU 
./process_mearec_sqmea.py $RESOURCE_CPU $RESOURCE_GPU 
./process_mearec_tetrode.py $RESOURCE_CPU $RESOURCE_GPU 

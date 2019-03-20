#!/bin/bash

#./process_magland_synth_test.py 
#./process_magland_synth.py ccmlin000-80 ccmlin000-parallel
#./process_visapy_mea.py ccmlin000-80 ccmlin000-parallel 
#./process_bionet.py ccmlin000-80 ccmlin000-parallel 

./process_mearec_tetrode.py ccmlin008-80 ccmlin008-parallel 
./process_manual_tetrode.py ccmlin008-80 ccmlin008-parallel 
./process_mearec_neuronexus.py ccmlin008-80 ccmlin008-parallel 
./process_mearec_sqmea.py ccmlin008-80 ccmlin008-parallel 
./process_paired.py ccmlin008-80 ccmlin008-parallel 
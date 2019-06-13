#!/bin/bash
set -e

./assemble_website_data.py \
    --upload_to spikeforest.kbucket,spikeforest.public \
    --dest_key_path key://pairio/spikeforest/spike-front-results-irc.json \
    --output_ids paired_boyden32c_irc,paired_crcns_irc,paired_mea64c_irc,paired_kampff_irc,synth_bionet_irc,synth_magland_irc,manual_franklab_irc,synth_mearec_neuronexus_irc,hybrid_janelia_irc

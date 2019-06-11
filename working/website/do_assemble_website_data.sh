#!/bin/bash
set -e

./assemble_website_data.py --upload_to spikeforest.kbucket,spikeforest.public --dest_key_path key://pairio/spikeforest/spike-front-results.json

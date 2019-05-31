#!/bin/bash
set -e

./assemble_website_data.py --upload_to spikeforest.kbucket --dest_key_path key://pairio/spikeforest/spike-front-results.json

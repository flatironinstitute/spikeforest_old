#!/bin/bash
set -e

./assemble_website_data.py --output_dir website_data --upload_to spikeforest.kbucket --dest_key_path key://pairio/spikeforest/spike-front-results.json

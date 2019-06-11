#!/bin/bash
set -e

cd ../website
if [ -d website_data ]; then rm -rf website_data; fi

./make_website_data_directory.py --download-from spikeforest.kbucket --key_path key://pairio/spikeforest/spike-front-results.json --output_dir website_data

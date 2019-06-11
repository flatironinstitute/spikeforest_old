#!/bin/bash
set -e

./make_website_data.sh

cd ../website
./load_data_into_local_database.sh website_data
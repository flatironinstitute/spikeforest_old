#!/bin/bash

# Use the following to connect to cairio
export KBUCKET_URL="http://localhost:63240"

export CAIRIO_URL="http://localhost:10001"
export CAIRIO_CONFIG="collection1.test-readwrite"
export CAIRIO_CONFIG_PASSWORD="test_password"

#export CAIRIO_URL="https://pairio.org:20443"
#export CAIRIO_CONFIG="test_collection1.test-readwrite-remote-cairio"
#export CAIRIO_CONFIG_PASSWORD="test_password"


# find containers (look in spikeforest2)
export CAIRIO_ALTERNATE_SHARE_IDS=69432e9201d0

python process_toy_example.py

#!/bin/bash


workdir=$PWD
cd ..
kbucketserver/bin/kbucket-hub kbucketserver/test_nodes/test_kbhub1 --auto &
kbucketserver/bin/kbucket-host kbucketserver/test_nodes/test_kbshare1 --auto &
export CAS_UPLOAD_DIR=kbucketserver/test_nodes/test_kbshare1/sha1-cache
export CAS_UPLOAD_TOKEN=test_upload_token
PORT=63250 node kbucketserver/src/casuploadserver/casuploadserver.js &

export CAIRIO_ADMIN_TOKEN="test_admin_token"
PORT=10001 node cairioserver/cairioserver/cairioserver.js &

sleep 3

cd $workdir
python setup_config.py &

# Use the following to connect to cairio
export KBUCKET_URL="http://localhost:63240"
export CAIRIO_URL="http://localhost:10001"
export CAIRIO_CONFIG="collection1.test-readwrite"
export CAIRIO_CONFIG_PASSWORD="test_password"

# find containers (look in spikeforest2)
export CAIRIO_ALTERNATE_SHARE_IDS=69432e9201d0

#######################################################
## Compute resource
export NUM_WORKERS=2
export MKL_NUM_THREADS=$NUM_WORKERS
export NUMEXPR_NUM_THREADS=$NUM_WORKERS
export OMP_NUM_THREADS=$NUM_WORKERS

../../bin/batcho_listen testing-resource --allow_uncontainerized &
#######################################################

sleep 2

python process_toy_example.py

# while true; do sleep 1; done
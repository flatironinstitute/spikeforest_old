#!/bin/bash

workdir=$PWD
cd ../../../mountaintools
kbucketserver/bin/kbucket-hub kbucketserver/test_nodes/test_kbhub1 --auto &
kbucketserver/bin/kbucket-host kbucketserver/test_nodes/test_kbshare1 --auto &
export CAS_UPLOAD_DIR=kbucketserver/test_nodes/test_kbshare1/sha1-cache
export CAS_UPLOAD_TOKEN=test_upload_token
PORT=63250 node kbucketserver/src/casuploadserver/casuploadserver.js &

CAIRIO_ADMIN_TOKEN="test_admin_token" PORT=10001 node cairioserver/cairioserver/cairioserver.js &

sleep 2

cd $workdir
python setup_config.py &

while true; do sleep 1; done

#!/bin/bash

set -e

export CAIRIO_ADMIN_TOKEN=$1
export MONGODB_URL=$2
export PORT=$3

node /src/cairioserver/cairioserver.js

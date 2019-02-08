#!/bin/bash
set -e

DEST=$1
RECIPE=$2

## This will be the command we run inside docker container
cmd="singularity build /tmp/out.simg $RECIPE"

## Run the command inside the docker container
docker rm build_sing || echo "."
docker run --privileged --userns=host --name build_sing -v $PWD:/working magland/singularity:2.6.0 \
  bash -c "$cmd"

echo "Copying file out of container"
docker cp build_sing:/tmp/out.simg $DEST

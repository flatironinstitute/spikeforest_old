#!/bin/bash

SHA1_CACHE_DIR="${SHA1_CACHE_DIR:-/tmp/sha1-cache}"
OUTPUT_DIR=$PWD/test1_docker_output
mkdir -p $OUTPUT_DIR
mkdir -p $SHA1_CACHE_DIR
docker run -it \
    -v /etc/passwd:/etc/passwd -u `id -u`:`id -g` \
    -e HOME=/tmp \
    -v ~/.kachery:/tmp/.kachery \
    -v $SHA1_CACHE_DIR:/tmp/sha1-cache \
    -v $OUTPUT_DIR:/output \
    magland/sf-spykingcircus \
    sha1dir://3ea5c9bd992de2d27402b2e83259c679d76e9319.synth_mearec_tetrode/datasets_noise10_K10_C4/001_synth
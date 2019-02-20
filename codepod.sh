#!/bin/bash
set -ex

## Open in codepod

OPTS=""

# KBucket cache directory
if [ ! -z "$KBUCKET_CACHE_DIR" ]; then
  OPTS="$OPTS -v $KBUCKET_CACHE_DIR:/tmp/sha1-cache -v /dev/shm:/dev/shm"
fi

eval "codepod -g -w $PWD $OPTS"

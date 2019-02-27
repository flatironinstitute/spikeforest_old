#!/bin/bash
set -ex

# Run this script to open the project in codepod
# To install codepod: pip install --upgrade codepod
# You must also have docker installed
# Once in codepod, you can, for exampe, open vscode: code .

OPTS=""

# KBucket cache directory
if [ ! -z "$KBUCKET_CACHE_DIR" ]; then
  OPTS="$OPTS -v $KBUCKET_CACHE_DIR:/tmp/sha1-cache -v /dev/shm:/dev/shm"
fi

eval "codepod -g -w $PWD $OPTS $@"

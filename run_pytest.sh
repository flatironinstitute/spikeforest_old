#!/bin/bash

# Run pytest with a clean temporary directory for MOUNTAIN_DIR and KBUCKET_CACHE_DIR
# You can still send command-line arguments

TEST_DIR=$PWD/tmp_pytest_working

if [ -d "TEST_DIR" ]; then
  rm -rf $TEST_DIR; 
fi

mkdir -p $TEST_DIR/.mountain
mkdir -p $TEST_DIR/sha1-cache
export MOUNTAIN_DIR=$TEST_DIR/.mountain
export KBUCKET_CACHE_DIR=$TEST_DIR/sha1-cache

pytest "$@"


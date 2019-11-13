#!/bin/bash
set -ex

# Run this script to open the project in codepod
# To install codepod: pip install --upgrade codepod
# You must also have docker installed
# Once in codepod, you can, for exampe, open vscode: code .

OPTS=""

# SHA-1 cache directory
if [ ! -z "$SHA1_CACHE_DIR" ]; then
  OPTS="$OPTS -v $SHA1_CACHE_DIR:/tmp/sha1-cache -v /dev/shm:/dev/shm"
fi

if [ -d "$HOME/.mountaintools" ]; then
  OPTS="$OPTS -v $HOME/.mountaintools:/home/user/.mountaintools"
fi

eval "codepod -g $PWD $OPTS $@"

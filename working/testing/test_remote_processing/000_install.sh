#!/bin/bash

pushd ../../../mountaintools
pushd kbucketserver
npm install
pushd src/casuploadserver
npm install
popd
popd
pushd cairioserver
npm install
popd
popd
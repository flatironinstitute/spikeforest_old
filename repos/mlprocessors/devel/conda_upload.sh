#!/bin/bash

hold="python devel/print_setup_py_data.py"

PACKAGE_NAME=`$hold | jq -r '.name'`
VERSION=`$hold | jq -r '.version'`
BUILD_NUMBER=`$hold | jq -r '.conda.build_number'`
UPLOAD_CHANNEL=`cat devel/conda_upload_config.json | jq -r '.anaconda_upload_channel'`
STR='py36'

cmd="anaconda upload $CONDA_PREFIX/conda-bld/linux-64/$PACKAGE_NAME-$VERSION-${STR}_${BUILD_NUMBER}.tar.bz2 -u $UPLOAD_CHANNEL"
echo $cmd
$cmd

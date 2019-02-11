#!/bin/bash

export CAIRIO_CONFIG="spikeforest.spikeforest2-readwrite"
export CAIRIO_CONFIG_PASSWORD="$SPIKEFOREST_PASSWORD"
../../../bin/batcho_listen jfm-laptop --parallel=4

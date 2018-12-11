#!/bin/bash

# Instructions:
#    You must first build or pull the magland/kbucket docker image
#    Then decide which directory you want to share. Let's call it /my/share
#    Run this script as follows:
#
#    ./docker_run_kbucket_share.sh /my/share
#
#    The first time, you will need to answer some questions, which sets some
#    configuration files in /my/share/.kbucket
#
#    On subsequent runs you will just need to run
#
#    ./docker_run_kbucket_share.sh /my/share --auto


docker run -v $1:/share -it magland/kbucket bash /scripts/kbucket_share.sh $2

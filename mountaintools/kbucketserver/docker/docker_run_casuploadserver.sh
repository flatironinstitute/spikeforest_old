#!/bin/bash

# INSTRUCTIONS:
#   You must first build or pull the magland/kbucket docker image
#   Then decide which directory you are going to use for the share. Let's call it /my/share
#   Create a /my/share/.env with the following content: (no leading spaces)
#
#   CAS_UPLOAD_TOKEN=[some-secret-token-of-your-choice]
#
#   Then run this script as follows:
#   ./docker_run_casuploadserver.sh /my/share [listen-port]


docker run -v $1:/share -p $2:24341 -it magland/kbucket bash /scripts/casuploadserver.sh

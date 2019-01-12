#!/bin/bash
set -e

../../docker/build_simg_using_docker.sh test_container.simg docker://magland/test_container

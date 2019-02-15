#!/bin/bash
set -ex

# These should already be installed from the container
./setup_python.sh

# Additional development packages
# pip install autopep8 # for formatting python code
#git config core.hooksPath .githooks
#pip install --upgrade nbstripout # for stripping output on .ipynb files

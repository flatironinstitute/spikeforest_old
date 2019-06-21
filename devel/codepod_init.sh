#!/bin/bash
set -ex

# This script is called when the gitpod container starts.
# It is called from the root directory of the project

pip install -e ./mountaintools
pip install -e ./spikeforest
pip install six

# vscode extensions
code --install-extension ms-python.python
code --install-extension eamodio.gitlens
code --install-extension bierner.markdown-preview-github-styles
# code --install-extension rduldulao.py-coverage-view

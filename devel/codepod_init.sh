#!/bin/bash
set -ex

# This script is called when the gitpod container starts.
# It is called from the root directory of the project

pip install -r requirements.txt
python setup.py develop

cd mountaintools
pip install -r requirements.txt
python setup.py develop

# vscode extensions
code --install-extension ms-python.python
code --install-extension eamodio.gitlens
# code --install-extension rduldulao.py-coverage-view

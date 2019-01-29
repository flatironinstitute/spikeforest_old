#!/bin/bash
set -ex

pip install -r requirements.txt
python setup.py develop
pip install jupyterlab

if [ -f /home_data/.gitconfig ]; then
    ln -s /home_data/.gitconfig ~/.gitconfig
fi

#!/bin/bash
set -ex

python setup.py develop

cd mountaintools
python setup.py develop

# somehow this is needed by jupyter lab
pip install six

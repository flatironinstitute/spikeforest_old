#!/bin/bash
set -ex

pip install -r requirements.txt
python setup.py develop

cd mountaintools
pip install -r requirements.txt
python setup.py develop

# somehow this is needed by jupyter lab
pip install six

# vscode extensions
code --install-extension ms-python.python
code --install-extension eamodio.gitlens
# code --install-extension rduldulao.py-coverage-view
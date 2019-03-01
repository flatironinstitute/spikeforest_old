#!/bin/bash
set -e
# ./setup_python.sh env_name

source ~/conda/etc/profile.d/conda.sh

CONDA_ENV=${1:-spikeforest}
conda deactivate
conda env remove -n $CONDA_ENV -y || echo "$CONDA_ENV conda environment not removed"

conda create -n $CONDA_ENV python=3.6 -y
conda activate $CONDA_ENV

BASEDIR=$(dirname "$0")

# This script is called when the gitpod container starts.
# It is called from the root directory of the project

pip install -r $BASEDIR/requirements.txt
pip install -e $BASEDIR/../mountaintools
pip install -e $BASEDIR/../spikeforest

conda install -c anaconda pyqt -y
# for issues relating to gui/sf_main/start_sf_main.py 
# follow instruction here https://github.com/Ultimaker/Cura/pull/131#issuecomment-176088664

# install jupyter extension
conda install -c conda-forge ipywidgets -y
jupyter labextension install @jupyter-widgets/jupyterlab-manager


# run test
pytest

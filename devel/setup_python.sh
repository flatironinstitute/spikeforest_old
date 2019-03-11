# run `. setup_python.sh`
# #!/bin/bash
# set -e
# ./setup_python.sh env_name

CONDA_ENV=${1:-spikeforest}
conda deactivate
conda env remove -n $CONDA_ENV -y || echo "$CONDA_ENV conda environment not removed. Try closing other terminals using $CONDA_ENV"

conda create -n $CONDA_ENV python=3.6 jupyterlab -y
conda activate $CONDA_ENV

## This script is called when the gitpod container starts.
## It is called from the root directory of the project
pip install -r devel/requirements.txt
pip install -e mountaintools/
pip install -e spikeforest/

conda install -c anaconda pyqt -y
## for issues relating to gui/sf_main/start_sf_main.py 
## follow instruction here https://github.com/Ultimaker/Cura/pull/131#issuecomment-176088664

## install jupyter extension
conda install -c conda-forge ipywidgets -y
jupyter labextension install @jupyter-widgets/jupyterlab-manager


## run test
pytest

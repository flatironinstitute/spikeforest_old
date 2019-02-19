## SpikeForest2

## Installation

(See below for instructions on opening this project in a docker container via codepod)

This is a meta repository that is meant to be used in development/editable mode.

To install using conda, first create a conda environment with python 3.6:

```
conda create -n spikeforest2 python=3.6
conda activate spikeforest2
```

Then run the following

```
# See: setup_python.sh
pip install -r requirements.txt
python setup.py develop

cd mountaintools
pip install -r requirements.txt
python setup.py develop
```

To run colab jupyter notebooks in a local runtime, we recommend chrome browser or chromium-browser. Firefox browser may not properly connect to the local runtime environment. You must run the following prior to using colab with a local runtime:

```
# colab (see setup_colab.sh)
pip install jupyter_http_over_ws
jupyter serverextension enable --py jupyter_http_over_ws
```

In addition, if you want to use some of the interactive graphics within jupyterlab, do the following:

```
./setup_jp_proxy_widget.sh
```

The repo/ directory contains a snapshot of a number of different dependent projects. These may or may not be up-to-date with the associated stand-alone packages. In this way, spikeforest2 is a snapshot project that contains all the necessary code, and is less susceptible to breaking changes in other packages.

## Installation using codepod

You can use spikeforest2 with codepod.

Prerequisites: [docker](https://docs.docker.com/) and [codepod](https://github.com/magland/codepod)

First clone this repo and checkout this branch (currently dev-unicorn):

```
git clone https://github.com/flatironinstitute/spikeforest2
git checkout -b dev-unicorn
```

Next, set the KBUCKET_CACHE_DIR environment variable. This is where the cached files from kbucket will go. For example, you could use `export KBUCKET_CACHE_DIR=/tmp/sha1-cache`

Then run the ./codepod.sh convenience script in the repo

```
cd spikeforest2 # make sure you are on the dev-unicorn branch
./codepod.sh
```

This will download a docker image and put you in a container where you can run
```
code .
```

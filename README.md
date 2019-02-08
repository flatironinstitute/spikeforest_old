## SpikeForest2

## Installation

(See below for instructions on opening this project in a docker container via theiapod)

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

Further documentation: [spikeforest-docs](https://github.com/flatironinstitute/spikeforest-docs/blob/master/docs/index.md)

## Installation using theiapod

You can use spikeforest2 with theiapod.

Prerequisites: [docker](https://docs.docker.com/) and [theiapod](https://github.com/magland/theiapod)

First clone this repo and checkout this branch (currently dev):

```
git clone https://github.com/flatironinstitute/spikeforest2
git checkout -b dev
```

Next, set the KBUCKET_CACHE_DIR environment variable. This is where the cached files from kbucket will go. For example, you could use `export KBUCKET_CACHE_DIR=/tmp/sha1-cache`

Then create and run a script such as the following.

```
#!/bin/bash
set -ex

OPTS=""

# Ports
OPTS="$OPTS --port 3000"

# git configuration
if [ -f "$HOME/.gitconfig" ]; then
  OPTS="$OPTS -v $HOME/.gitconfig:/home/theiapod/.gitconfig"
fi
if [ -d "$HOME/.git-credential-cache" ]; then
  OPTS="$OPTS -v $HOME/.git-credential-cache:/home/theiapod/.git-credential-cache"
fi

# KBucket cache directory
if [ ! -z "$KBUCKET_CACHE_DIR" ]; then
  OPTS="$OPTS -v $KBUCKET_CACHE_DIR:/tmp/sha1-cache"
fi

# Need --privileged in order to run singularity containers
OPTS="$OPTS --docker_opts \"--privileged\""

# Run the container
theiapod -w $PWD/spikeforest2 $OPTS
```

This will create a container with the theia browser-based IDE. You can then start interacting with the project by pointing your web browser (preferably chrome) to `http://localhost:3000`.

You run jupyter lab or other web services within the container and then connect to them via other tabs in your web browser.

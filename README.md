## SpikeForest2
[![Build Status](https://travis-ci.org/flatironinstitute/spikeforest2.svg?branch=master)](https://travis-ci.org/flatironinstitute/spikeforest2)

**Note**: *This software is in alpha stage of development*

## Opening in codepod (containerized VS Code IDE)

(See also "Alternative installation" below)

You can use and/or develop SpikeForest2 with codepod. Tested in Linux, should also work on a Mac.

Prerequisites: [docker](https://docs.docker.com/) and [codepod](https://github.com/magland/codepod)

First clone this repo:

```
git clone https://github.com/flatironinstitute/spikeforest2
```

Next, set the KBUCKET_CACHE_DIR environment variable. This is where the cached files from kbucket will go. For example, you could use `export KBUCKET_CACHE_DIR=/tmp/sha1-cache`

If you want to use a conda virtual environment (e.g. `sf2`), run 
```
conda create -n sf2 python=3.6 jupyterlab
conda activate sf2
```

Install codepod
```
pip install spikeforest2
```

Then run the ./codepod_run.sh convenience script in the repo

```
cd spikeforest2
./codepod_run.sh
```

This will download a docker image (may take some time depending on your internet connection) and put you in a container with a fully-functional development environment.

Once inside the container you can run the following to open vscode
```
code .
```

## Unit tests

Once in codepod, you may run the unit tests via

```
pytest
```

To run the slower, more thorough, tests:
```
pytest -m slow -s
# The -s flag is for verbose output, which may not be what you want
# This will download singularity containers, which may take some time
# depending on your internet connection
```

## Directory structure

(Please notify if the following gets out-of-sync with the project directory structure)

`devel`: Utilities specific to development of SpikeForest, including instructions on preparing the docker image for codepod, a script to run when codepod is started, and a script for auto-formatting the python code for pep8 compliance.

`mountaintools`: Contains the MountainTools such as batcho, cairio, kbucket, mlprocessors, and vdomr. These tools are not specific to spike sorting.

`repos`: Related repositories. See note below.

`simplot`: A work-in-progress JavaScript library for interactive plotting.

`spikextractors`: A snapshot of the SpikeExtractors project.

`spikeforest`: A python module used for both spike sorting and visualization.

`spikeforest_analysis`: A python module using by spike sorting scripts and analysis scripts. Contains the core processing routines.

`spikeforestwidgets`: Some vdomr widgets used by the GUIs.

`spikesorters`: Wrappers of the spike sorting algorithms.

`spiketoolkit`: An old snapshot of the SpikeToolkit project.

`spikewidgets`: An old snapshot of the SpikeWidgets project.

`working`: The SpikeForest analysis scripts. Contains scripts for preparing recordings, running spike sorting, comparing with ground truth, and assembling results for the websites.

`.codepod.yml`: Configuration file for codepod

`.gitignore`: Files that git should ignore

`codepod_run.sh`: Run this to open the project using codepod (see above).

`pytest.ini`: Configuration file for pytest

`README.md`: This readme file

`LICENSE`: The license file for this project. See also license files for individual components within subdirectories.

`requirements.txt`: The python package dependencies

`setup_colab.sh`: Convenience script to set up a google colaboratory runtime

`setup_jp_proxy_widget.sh`: Convenience script for using vdomr in jupyter notebooks

`setup_python.sh`: Convenience script for installing python dependencies (not necessary when using codepod, see below)

`setup.py`: The setup file for this python package (see below)

## Alternative installation (not using codepod)

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

To run GUI tools, run
```
conda install -c anaconda pyqt
```
and test using
```
gui/sfbrowser/start_sfbrowser.py
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


## SpikeForest
[![Build Status](https://travis-ci.org/flatironinstitute/spikeforest.svg?branch=master)](https://travis-ci.org/flatironinstitute/spikeforest)

**Note**: *This project is in alpha stage of development*

## Overview

This software supports the SpikeForest web site (in progress) for public validation and comparison of spike sorting algorithms applied to an expanding collection of hosted  electrophysiology recordings with ground-truth spiking information. But you can also use this project for your own spike sorting, using MountainSort, IronClust, and other algorithms. 

The framework that supports the requirements of the website, including wrapping of spike sorters in singularity containers and python classes, job batching, comparison with ground truth, and processing using remote compute resources, is all open source and may be of benefit to neuroscience labs.

We make use of the [SpikeInterface](https://github.com/SpikeInterface/) project, also in alpha development stage, that provides tools for extracting, converting between, and curating raw or spike sorted extracellular data from any file format.

This repository is split into two pieces: MountainTools and SpikeForest. The former is not spike-sorting specific and can be used for other applications or downstream analyses. It provides modules for batch processing, automatic caching of results, sharing data between labs (from a python interface), and processing on remote compute resources. The latter contains wrappers to the spike sorters, analysis routines, GUI components, and the actual scripts used to prepare the data hosted on the website.

The code for the front-end website is also open source, but is hosted in a separate repository.

## Installation

It is recommended that you start from a fresh conda environment with python (>= 3.6) installed.

```
pip install git+https://github.com/flatironinstitute/spikeforest#subdirectory=spikeforest
pip install git+https://github.com/flatironinstitute/spikeforest#subdirectory=mountaintools
```

If you want to use the containerized versions of the spike sorters, you should install singularity. [link to instructions] Otherwise you will need to install the sorters individually. You can install MountainSort4 via

```
pip install ml_ms4alg
```

In the future we will provide conda packages for these.

### Installation for developers
Run [`devel/setup_python.sh`](https://github.com/flatironinstitute/spikeforest/blob/master/devel/setup_python.sh) to setup a conda environment (default is `spikeforest`) unless you specify an environment (e.g. `devel/setup_python my_env`). It will install all [necessary dependencies](https://github.com/flatironinstitute/spikeforest/blob/master/devel/requirements.txt) to develop and use SpikeForest.

[Pre-requisits]
1. CONDA: `setup_python.sh` uses conda installed in `~/conda/etc/profile.d/conda.sh`. Change this line to point to the correct conda location (see your `~/.bashrc`).
1. `ml_ms4alg` requires `g++` installation which may not be part of your OS. If this is the case, run `sudo apt install build-essential`.
1. jupyter notebooks use ipywidgets which requires `nodejs` installation. Run `sudo apt install nodejs npm -y` if you don't already have the nodejs installed.

### Installation in Windows 10 using Ubuntu WSL
1. Install Windows Subsystem for Linux (WSL). Run `Turn Windows features on or off` and check `Windows Subsystem for Linux`
1. Install Ubuntu 18.04 though the Microsoft store app
1. Start Ubuntu and install [Miniconda for Linux](https://docs.conda.io/en/latest/miniconda.html)
1. Run `sudo apt install build-essential nodejs npm -y`
1. Modify `devel/setup_python.sh` to point to the correct conda.sh (e.g. ` ~/miniconda3/etc/profile.d/conda.sh`)
1. Run `devel/setup_python.sh`
1. Test if installed correctly by running one of the example notebook. Run `conda activate spikeforest` and run `jupyter lab --no-browser` and copy the link. Paste in Chrome browser in Windows

## Basic usage

![Basic flow chart - SpikeForest](docs/basic_flow_chart_spikeforest.jpg?raw=true "Basic flow chart - SpikeForest")

There are various ways to use MountainTools and SpikeForest as illustrated in the above diagram. Here we describe a few of the use cases.

## Sorting a single recording

We start with the simplest case of a single recording.

* Step 1: prepare your recording in mda format

[pull text for elsewhere here]

* Step 2: run spike sorting

```
from spikesorters import MountainSort4

MountainSort4.execute(
    recording_dir=<recording directory>,
    firings_out=<output directory>/firings.mda,
    detect_sign=-1,
    adjacency_radius=50,
    _container=None
)
```

By specifying `_container=None` the system will attempt to run the spike sorting using software installed on your system, so you would need to have the `ml_ms4alg` python package installed. If you instead specified `_container='default'`, the appropriate singularity container would be automatically downloaded. In that case you would need to have singularity installed.

[Example notebook: `example_single_recording.ipynb`](https://github.com/flatironinstitute/spikeforest/blob/master/docs/example_notebooks/example_single_recording.ipynb)

## Sorting with any spike sorter

You can use spikeforest to run other spike sorters as well. For example, to run spyking circus, first follow the preliminary steps above, and then:

```
from spikesorters import SpykingCircus

SpykingCircus.execute(
    recording_dir=<recording directory>,
    firings_out=<output directory>/firings.mda,
    detect_sign=-1,
    adjacency_radius=50,
    _container='default' # To fetch the default container for spyking circus
)
```

As described above, by using `_container='default'` you do not need to install spyking circus, although if you do have spyking circus on your machine, you could simply use `_container=None`.

Other spike sorters in progress include YASS, KiloSort, and IronClust.

## Sorting batches of multiple recordings

[TODO: write this]

[Example notebook: `example_multi_recording.ipynb`](https://github.com/flatironinstitute/spikeforest/blob/master/docs/example_notebooks/example_multi_recording.ipynb)

## Sorting using a remote compute resource

[TODO: write this]

## Visualization of recordings and sorting results

[TODO: write this]

## Data sharing

[TODO: write this]

## For developers and testers: Opening in codepod (containerized VS Code IDE)

You can use and/or develop SpikeForest2 with codepod. Tested in Linux, should also work on a Mac but probably requires some tweaks.

Prerequisites: [docker](https://docs.docker.com/) and [codepod](https://github.com/magland/codepod)

First clone this repo:

```
git clone https://github.com/flatironinstitute/spikeforest
```

Next, set the KBUCKET_CACHE_DIR environment variable. This is where the cached files from kbucket will go. For example, you could use `export KBUCKET_CACHE_DIR=/tmp/sha1-cache`

Install codepod
```
pip install --upgrade codepod
```

Then run the ./codepod_run.sh convenience script in the repo

```
cd spikeforest
./codepod_run.sh
```

This will download a docker image (may take some time depending on the speed of your internet connection) and put you in a container with a fully-functional development environment.

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

`spikeforest/spikesorters`: Wrappers of the spike sorting algorithms.

`working`: The SpikeForest analysis scripts. Contains scripts for preparing recordings, running spike sorting, comparing with ground truth, and assembling results for the websites.

`spikeforest/spikeforest_analysis`: A python module using by spike sorting scripts and analysis scripts. Contains the core processing routines.

`spikeforest/spikeforestwidgets`: Some vdomr widgets used by the GUIs.

`.codepod.yml`: Configuration file for codepod

`.gitignore`: Files that git should ignore

`codepod_run.sh`: Run this to open the project using codepod (see above).

`pytest.ini`: Configuration file for pytest

`README.md`: This readme file

`LICENSE`: The license file for this project. See also license files for individual components within subdirectories.




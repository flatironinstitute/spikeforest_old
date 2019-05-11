## SpikeForest

## Overview

 #marker:29426aa5-spikeforest-overview

SpikeForest is a reproducible, continuously updating platform which benchmarks the performance of spike sorting codes across a large curated database of electrophysiological recordings with ground truth. It consists of an interactive website that presents our up-to-date findings (front-end source code hosted elsewhere), this python package which contains the tools for running the SpikeForest analysis, and an expanding collection of electrophysiology recordings with ground-truth spiking information.

The repository is split into three main directories: `spikeforest`, `mountaintools`, and `working`. MountainTools is not spike-sorting specific and can be used for other applications or downstream analyses. It provides modules for batch processing, automatic caching of results, sharing data between labs (from a python interface), and processing on remote compute resources. The `spikeforest` directory (SpikeForest package) contains wrappers to the spike sorters, analysis routines, GUI components. The `working` directory contains the actual scripts used to prepare the data hosted on the website.

We make use of the [SpikeInterface](https://github.com/SpikeInterface/) project, also in early development stage, that provides tools for extracting, converting between, and curating raw or spike sorted extracellular data from any file format.


## Installation from PyPI

 #marker:a11c726a-spikeforest-pypi-installation

To install SpikeForest from PyPI, it is recommended that you start from a fresh conda environment with python (>= 3.6).

```
pip install --upgrade spikeforest
pip install --upgrade mountaintools
```

Test the installation by sorting one of the toy examples as described below.

## Development installation

 #marker:471ab3bd-spikeforest-development-installation

To install SpikeForest for development on Linux, it is recommended that you start from a fresh conda environment with python (>= 3.6).

Then clone the repository and install the two packages in editable mode.

```
git clone https://github.com/flatironinstitute/spikeforest
cd spikeforest
pip install -e ./spikeforest
pip install -e ./mountaintools
```

This will install all of the python dependencies from PyPI as well as editable (local) versions of the spikeforest and mountaintools packages. Thus if you edit the source code, your changes will take effect on your local system.

To get development updates you can git pull the master branch and then reissue the pip install commands in case any of the python dependencies have changed:

```
git pull
pip install --upgrade -e ./spikeforest
pip install --upgrade -e ./mountaintools
```

Test the installation by sorting one of the toy examples as described below.

## Spike sorting

 #marker:d78156d4-spikeforest-spike-sorting

To use the containerized versions of the spike sorters (recommended), you should [install singularity](https://www.sylabs.io/guides/3.0/user-guide/quick_start.html#quick-installation-steps). This will work for all of the non-Matlab spike sorters (in the future we will also containerize the Matlab packages).

If you choose not to use the containerized sorters, then you will need to install each of the spike sorters individually. Instructions for doing this are found below.

Then the simplest way to perform spike sorting is:

```
from spikesorters import MountainSort4

MountainSort4.execute(
    recording_dir='<recording directory>',
    firings_out='<output directory>/firings.mda',
    detect_sign=-1,
    adjacency_radius=50,
    _container='default'  # Use _container=None to run without singularity
)
```

Here `'<recording_directory>'` must contain your ephys recording in .mda format. Instructions for preparing your data in this format using SpikeExtractors are found below.

The output (in `firings.mda` format) will be written to the `<output directory>/firings.mda` file.

To load the results, it is recommended that you use the [SpikeExtractors](https://github.com/SpikeInterface/SpikeExtractors) package.

```
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor

dsdir = '<recording directory>'
firings_fname = '<output directory>/firings.mda'

recording = SFMdaRecordingExtractor(dataset_directory=dsdir)
sorting = SFMdaSortingExtractor(firings_file=firings_fname)
```

See [SpikeExtractors](https://github.com/SpikeInterface/SpikeExtractors) for more information on using recording and sorting extractors.

To use other spike sorters, simply swap in the appropriate class. For example:

```
from spikesorters import SpykingCircus

SpykingCircus.execute(
    recording_dir='<recording directory>',
    firings_out='<output directory>/firings.mda',
    detect_sign=-1,
    adjacency_radius=50,
    _container='default'  # Use _container=None to run without singularity
)
```

## Preparing recordings in .mda format

 #marker:5ee480a5-spikeforest-preparing-recordings-mda

To create a recording in .mda format (suitable for running SpikeForest sorters), use the SpikeExtractors package, which should be installed as part of the SpikeForest installation.


## Installing the spike sorters

 #marker:3c4647e4-spikeforest-sorter-installation

If you choose not to use the singularity method, you can install the spike sorters individually as follows.

## HerdingSpikes2

See the [HerdingSpikes2 website](https://github.com/mhhennig/HS2) and the following [Dockerfile](https://github.com/flatironinstitute/spikeforest/blob/master/).

### IronClust

IronClust is a Matlab project. To use it with SpikeForest, first clone the repo and then set an environment variable pointing to the source location:

```
git clone https://github.com/jamesjun/ironclust
export IRONCLUST_PATH=<source location>
```

It is recommended that you add the `export` line to your `.bashrc` file.

### JRClust

Installation is similar to IronClust, except there is an additional environment variable to set (which will be documented soon).

```
git clone https://github.com/JaneliaSciComp/JRCLUST
export JRCLUST_PATH=<source location>
```

### KiloSort

Installation is similar to IronClust, except you also need to compile the CUDA code.

```
git clone https://github.com/cortex-lab/KiloSort
export KILOSORT_PATH=<source location>
```

Compilation instructions may be found on the KiloSort website.

### KiloSort2

Installation is similar to IronClust, except you also need to compile the CUDA code.

```
git clone https://github.com/MouseLand/Kilosort2
export KILOSORT2_PATH=<source location>
```

Compilation instructions may be found on the KiloSort website.

Note that we encountered some issues with KiloSort2 and are presently using a forked version (more details will be provided later).


### MountainSort4

```
pip install --upgrade ml_ms4alg
```

or see the following [Dockerfile](https://github.com/flatironinstitute/spikeforest/blob/master/).

### SpykingCircus

See the [SpykingCircus website](https://spyking-circus.readthedocs.io/en/latest/) and the following [Dockerfile](https://github.com/flatironinstitute/spikeforest/blob/master/).

### Tridesclous

See the [Tridesclous website](https://github.com/tridesclous/tridesclous).

### YASS

See the [YASS website](https://yass.readthedocs.io/en/latest/) and the following [Dockerfile](https://github.com/flatironinstitute/spikeforest/blob/master/).





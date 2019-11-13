## For developers and testers: Opening in codepod (containerized VS Code IDE)

 <!--- #marker:7d3f190c-spikeforest-codepod -->

You can use and/or develop SpikeForest with codepod. Tested in Linux, should also work on a Mac but probably requires some tweaks.

Prerequisites: [docker](https://docs.docker.com/) and [codepod](https://github.com/magland/codepod)

First clone this repo:

```
git clone https://github.com/flatironinstitute/spikeforest
```

Next, set the SHA1_CACHE_DIR environment variable. This is where the cached files from kbucket will go. For example, you could use `export SHA1_CACHE_DIR=/tmp/sha1-cache`

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

 <!--- #marker:e1d2a5e0-spikeforest-unit-tests -->

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

## Installation for developers (without using codepod)
Once installing dependencies below, run [`. devel/setup_python.sh`](https://github.com/flatironinstitute/spikeforest/blob/master/devel/setup_python.sh) from the main `spikeforest` directory to setup the conda environment.
- Default conda environment is named to `spikeforest` unless you specify an argument (e.g. `. devel/setup_python.sh my_env`)
- The script installs all [necessary dependencies](https://github.com/flatironinstitute/spikeforest/blob/master/devel/requirements.txt) for developing and using SpikeForest.

### Dependencies
1. CONDA: `setup_python.sh` uses conda installed in `~/conda/etc/profile.d/conda.sh`. Change this line to point to the correct conda location (see your `~/.bashrc`).
1. `ml_ms4alg` requires `g++` installation which may not be part of your OS. If this is the case, run `sudo apt install build-essential`.
1. `nodejs` to use `ipywidgets` in jupyter notebooks. To install `nodejs`, run `sudo apt install nodejs npm -y`.
1. Install [`docker`](https://www.digitalocean.com/community/tutorials/how-to-install-and-use-docker-on-ubuntu-18-04) and [`singularity`](https://www.sylabs.io/guides/3.0/user-guide/quick_start.html#quick-installation-steps)

## Installation in Windows 10 using Ubuntu WSL
1. Install Windows Subsystem for Linux (WSL). Run `Turn Windows features on or off` and check `Windows Subsystem for Linux`
1. Install Ubuntu 18.04 though the Microsoft store app
1. Start Ubuntu and install [Miniconda for Linux](https://docs.conda.io/en/latest/miniconda.html)
1. Run `sudo apt install build-essential nodejs npm -y`
1. Modify `devel/setup_python.sh` to point to the correct conda.sh (e.g. ` ~/miniconda3/etc/profile.d/conda.sh`)
1. Run `devel/setup_python.sh`
1. Test if installed correctly by running one of the example notebook. Run `conda activate spikeforest` and run `jupyter lab --no-browser` and copy the link. Paste in Chrome browser in Windows
```
# MountainTools

A collection of tools for creating shareable and reproducible scientific workflows. It is used by [SpikeForest](https://github.com/flatironinstitute/spikeforest).

MountainTools provides

* A formal method for defining well-defined Python procedures that operate on input parameters and files and produce output files. These are known as *Processors*.
* Automatic execution of *Processors* inside [singularity](https://sylabs.io/docs/) containers
* Automatic caching of results from *Processor* runs
* Job management, batching, and queing mechanisms for *Processor* runs
* Parallelization capabilities and automated running of processing batches on compute clusters
* Functions for storing files, text, and objects (JSON-serializable Python dicts) in local and remote databases
* Content-addressible storage databases (kacheries)
* A key/value storage database (pairio)
* Tools for working with `sha1://` and `sha1dir://` URIs

The Python package is installable via

```
pip install mountaintools
```

and comprises the following modules:

* [**mlprocessors**](mlprocessors/README.md) - utilities for MountainTools *Processors*, jobs, batches, parallelization, and running batches on a compute cluster
* [**mountainclient**](mountainclient/README.md) - for working with `sha1://` and `sha1dir://` URIs, accessing the local MountainTools databases, and interacting with remote kacheries (content-addressible storage databases).
* [**vdomr**](vdomr) - for building GUIs using a mix of Python and JavaScript that may be run in notebooks, in the browser, or on the desktop. This will eventually be separated out and maintained as its own Python package.

This repository also contains JavaScript / NodeJS code for running pairio and kachery servers.

## Installation
To install mountaintools the easiest approach is to use pip. Open your terminal emulator and type in the following command:
```
pip install mountaintools
```

**Note:** Depending on your environment you might need to substitute `pip` with `pip3` as mountaintools works only with Python 3.

For information on using mountaintools see [mountainclient](mountainclient), [mlprocessors](mlprocessors), and [vdomr](vdomr).

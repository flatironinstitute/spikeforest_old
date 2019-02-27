# Spike sorting

## Simplest case: sorting a single recording

* Step 0: Install the software

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

By using `_container='default'` you do not need to install spyking circus, although if you do have spyking circus on your machine, you could simply use `_container=None`.

Other spike sorters are in progress (YASS, KiloSort, IronClust).

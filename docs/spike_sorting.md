# Spike sorting

## Simplest case: sorting a single recording

* Step 0: Install the software

```
describe this
```

In the future we will provide conda packages

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

By using `_container='default'` you do not need to install spyking circus, although if you do have spiking circus on your machine, you could simply use `_container=None`.

Other spike sorters are in progress (YASS, KiloSort, IronClust).

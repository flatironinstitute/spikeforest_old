# Spike sorting a SpikeForest recording

A subset of the recordings featured on the SpikeForest website are available for
public download using our Python interface. Here we describe how to download and
perform spike sorting on one of these recordings.

After installation, the below code may be run via [this python file](spike_sorting_spikeforest_recording.py).

## Prerequisites

At this point, SpikeForest has only been tested in Linux. It should be straightforward to adapt
to OS X. It is also possible to use Linux within Windows.

## Installation

The first step is to install spikeforest and mountaintools. The easiest way is to use
the PyPI packages as follows.

```
pip install --upgrade spikeforest==0.6.1
pip install --upgrade mountaintools==0.3.0
```

To use the containerized versions of the spike sorters (recommended), you should
[install
singularity](https://www.sylabs.io/guides/3.0/user-guide/quick_start.html#quick-installation-steps).
This will work for all of the non-Matlab spike sorters (in the future we will
also containerize the Matlab packages).

## Downloading a recording

To download a SpikeForest recording, you will first need to know its `sha1dir://` URI. Presently there
is no method for obtaining this via the website, although we will provide this feature in an upcoming
release. However, we provide some test examples here.

Making use of [SpikeInterface](https://github.com/SpikeInterface/), we can load the recording and the ground truth sorting in Python:

```python
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
from mountaintools import client as mt

# Configure to download from the public spikeforest kachery node
mt.configDownloadFrom('spikeforest.public')

# Load an example tetrode recording with its ground truth
recdir = 'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C4/001_synth'

print('Load recording...')
recording = SFMdaRecordingExtractor(dataset_directory=recdir, download=True)
sorting_true = SFMdaSortingExtractor(firings_file=recdir + '/firings_true.mda')
```

This will automatically download the necessary files and you now have objects
representing the recording and ground truth sorting which you can manipulate
using the tools of [SpikeInterface](https://github.com/SpikeInterface/).

For our purposes, we will operate directly on the recording directory in order
to take advantage of the MountainTools caching and container capabilities. But
in the future we will be able to perform these operations directly using the
extractor objects.

```python
# import a spike sorter from the spikesorters module of spikeforest
from spikesorters import MountainSort4
import os

# In place of MountainSort4 you could use any of the following:
#
# MountainSort4, SpykingCircus, KiloSort, KiloSort2, YASS
# IronClust, HerdingSpikes2, JRClust, Tridesclous, Klusta
# although the Matlab sorters require further setup.

# create an output directory if does not exist (keep things tidy)
os.makedirs('outputs', exist_ok=True)

# Run spike sorting in the default singularity container
print('Spike sorting...')
MountainSort4.execute(
    recording_dir=recdir,
    firings_out='outputs/ms4_firings.mda',
    detect_sign=-1,
    adjacency_radius=50,
    _container='default'
)

# Load the result into a sorting extractor
sorting = SFMdaSortingExtractor(firings_file='outputs/ms4_firings.mda')
```

Note that when using MountainTools processors (via `execute()`), results are
automatically cached. To force rerun, use the `_force_run=True` option.

As mentioned in the comments above, you can use any of the SpikeForest-wrapped
sorting algorithms in place of MountainSort4.

Next, we can compare the result with ground truth

```python
# import from the spikeforest package
import spikeforest_analysis as sa

# write the ground truth firings file
SFMdaSortingExtractor.write_sorting(
    sorting=sorting_true,
    save_path='outputs/firings_true.mda'
)

# run the comparison
print('Compare with truth...')
sa.GenSortingComparisonTable.execute(
    firings='outputs/ms4_firings.mda',
    firings_true='outputs/firings_true.mda',
    units_true=[],  # use all units
    json_out='outputs/comparison.json',
    html_out='outputs/comparison.html',
    _container=None
)

# we may also want to compute the SNRs of the ground truth units
# together with firing rates and other information
print('Compute units info...')
sa.ComputeUnitsInfo.execute(
    recording_dir=recdir,
    firings='outputs/firings_true.mda',
    json_out='outputs/true_units_info.json'
)

# Now you may inspect outputs/comparison.html (in a browser)
# and outputs/true_units_info.json

```
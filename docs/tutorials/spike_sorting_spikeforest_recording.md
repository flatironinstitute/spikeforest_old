# Spike sorting a SpikeForest recording

A subset of the recordings featured on the SpikeForest website are available for
public download using our Python interface. Here we describe how to download and
perform spike sorting on one of these recordings.

After installation, the below code may be run via [this python file](spike_sorting_spikeforest_recording.py).

## Prerequisites

At this point, SpikeForest has only been tested in Linux. In the future we will support OSX. It is also possible to use Linux within Windows.


## Installation

The first step is to install spikeforest and mountaintools. The easiest way is to use
the PyPI packages as follows.

```
pip install --upgrade spikeforest==0.10.3
pip install --upgrade mountaintools==0.7.0
```

To use the containerized versions of the spike sorters (recommended), you should
[install singularity 2.6.1](https://www.sylabs.io/guides/2.6/user-guide/quick_start.html#quick-installation-steps).
This will work for all of the non-Matlab spike sorters (in the future we will
also containerize the Matlab packages).

## Downloading a recording

To download a SpikeForest recording, you will first need to know its
`sha1dir://` address. For testing purposes we provide a subset of recordings that
are available for public download via `sha1dir://...`. See the bottom of this
file for the list of such recordings available for testing.

Making use of [SpikeInterface](https://github.com/SpikeInterface/), we can load the recording and the ground truth sorting in Python:

```python
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
from mountaintools import client as mt

# Configure to download from the public spikeforest kachery node
mt.configDownloadFrom('spikeforest.public')

# Load an example tetrode recording with its ground truth
# You can also substitute any of the other available recordings
recdir = 'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C4/001_synth'

print('loading recording...')
recording = SFMdaRecordingExtractor(dataset_directory=recdir, download=True)
sorting_true = SFMdaSortingExtractor(firings_file=recdir + '/firings_true.mda')
```

This will automatically download the necessary files and you now have objects
representing the recording and ground truth sorting which you can manipulate
using the tools of [SpikeInterface](https://github.com/SpikeInterface/).

## Running the sorting

For our purposes, we will operate directly on the recording directory in order
to take advantage of the MountainTools caching and container capabilities. But
in the future we will be able to perform these operations directly using the
extractor objects.

```python
# import a spike sorter from the spikesorters module of spikeforest
from spikesorters import MountainSort4
import os
import shutil

# In place of MountainSort4 you could use any of the following:
#
# MountainSort4, SpykingCircus, KiloSort, KiloSort2, YASS
# IronClust, HerdingSpikes2, JRClust, Tridesclous, Klusta
# although the Matlab sorters require further setup.

# clear and create an empty output directory (keep things tidy)
if os.path.exists('test_outputs'):
    shutil.rmtree('test_outputs')
os.makedirs('test_outputs', exist_ok=True)

# Run spike sorting in the default singularity container
print('Spike sorting...')
MountainSort4.execute(
    recording_dir=recdir,
    firings_out='test_outputs/ms4_firings.mda',
    detect_sign=-1,
    adjacency_radius=50,
    _container='default'
)

# Load the result into a sorting extractor
sorting = SFMdaSortingExtractor(firings_file='test_outputs/ms4_firings.mda')
```

When using MountainTools processors (via `execute()`), results are
automatically cached. To force rerun, use the `_force_run=True` option.

As mentioned in the comments above, you can use any of the SpikeForest-wrapped
sorting algorithms in place of MountainSort4.

## Comparison with ground truth

Next, we can compare the result with ground truth

```python
# import from the spikeforest package
import spikeforest_analysis as sa

# write the ground truth firings file
SFMdaSortingExtractor.write_sorting(
    sorting=sorting_true,
    save_path='test_outputs/firings_true.mda'
)

# run the comparison
print('Compare with truth...')
sa.GenSortingComparisonTable.execute(
    firings='test_outputs/ms4_firings.mda',
    firings_true='test_outputs/firings_true.mda',
    units_true=[],  # use all units
    json_out='test_outputs/comparison.json',
    html_out='test_outputs/comparison.html',
    _container=None
)

# we may also want to compute the SNRs of the ground truth units
# together with firing rates and other information
print('Compute units info...')
sa.ComputeUnitsInfo.execute(
    recording_dir=recdir,
    firings='test_outputs/firings_true.mda',
    json_out='test_outputs/true_units_info.json'
)

import numpy as np

# Load and consolidate the outputs
true_units_info = mt.loadObject(path='test_outputs/true_units_info.json')
comparison = mt.loadObject(path='test_outputs/comparison.json')
true_units_info_by_unit_id = dict()
for unit in true_units_info:
  true_units_info_by_unit_id[unit['unit_id']] = unit
for unit in comparison.values():
  unit['true_unit_info'] = true_units_info_by_unit_id[unit['unit_id']]
  
# Print SNRs and accuracies
for unit in comparison.values():
  print('Unit {}: SNR={}, accuracy={}'.format(unit['unit_id'], unit['true_unit_info']['snr'], unit['accuracy']))
  
# Report number of units found
snrthresh = 8
units_above = [unit for unit in comparison.values() if float(unit['true_unit_info']['snr'] > snrthresh)]
print('Avg. accuracy for units with snr >= {}: {}'.format(snrthresh, np.mean([float(unit['accuracy']) for unit in units_above])))

```

## Recordings publicly available for testing

The following recordings are publicly available for testing and may
be substituted in the script above.

- PAIRED_CRCNS_HC1/paired_crcns/d11221_d11221.001: `sha1dir://779d96521176077ec260ef99573dea3b772c74e6.paired_crcns/d11221_d11221.001`
- PAIRED_MEA64C_YGER/paired_mea64c/20160415_patch2: `sha1dir://cd5ba0215df92e1b9309d89f89590013276116cc.paired_mea64c/20160415_patch2`
- PAIRED_KAMPFF/paired_kampff/2014_11_25_Pair_3_0: `sha1dir://51570fce195942dcb9d6228880310e1f4ca1395b.paired_kampff/2014_11_25_Pair_3_0`
- SYNTH_BIONET/synth_bionet_static/static_8x_A_2A: `sha1dir://abc900f5cd62436e7c89d914c9f36dcd7fcca0e7.synth_bionet/bionet_static/static_8x_A_2A`
- SYNTH_BIONET/synth_bionet_drift/drift_8x_A_2A: `sha1dir://abc900f5cd62436e7c89d914c9f36dcd7fcca0e7.synth_bionet/bionet_drift/drift_8x_A_2A`
- SYNTH_BIONET/synth_bionet_shuffle/shuffle_8x_A_2A: `sha1dir://abc900f5cd62436e7c89d914c9f36dcd7fcca0e7.synth_bionet/bionet_shuffle/shuffle_8x_A_2A`
- SYNTH_MAGLAND/synth_magland_noise10_K10_C4/001_synth: `sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C4/001_synth`
- SYNTH_MAGLAND/synth_magland_noise10_K10_C8/001_synth: `sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C8/001_synth`
- SYNTH_MAGLAND/synth_magland_noise10_K20_C4/001_synth: `sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K20_C4/001_synth`
- SYNTH_MAGLAND/synth_magland_noise10_K20_C8/001_synth: `sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K20_C8/001_synth`
- SYNTH_MAGLAND/synth_magland_noise20_K10_C4/001_synth: `sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise20_K10_C4/001_synth`
- SYNTH_MAGLAND/synth_magland_noise20_K10_C8/001_synth: `sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise20_K10_C8/001_synth`
- SYNTH_MAGLAND/synth_magland_noise20_K20_C4/001_synth: `sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise20_K20_C4/001_synth`
- SYNTH_MAGLAND/synth_magland_noise20_K20_C8/001_synth: `sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise20_K20_C8/001_synth`
- MANUAL_FRANKLAB/manual_tetrode_600s/sorter1_1: `sha1dir://b1618868a12e92d8fb5df2b60b34dc0716a40552.manual_franklab/tetrode_600s/sorter1_1`
- MANUAL_FRANKLAB/manual_tetrode_1200s/sorter1_1: `sha1dir://b1618868a12e92d8fb5df2b60b34dc0716a40552.manual_franklab/tetrode_1200s/sorter1_1`
- MANUAL_FRANKLAB/manual_tetrode_2400s/sorter1_1: `sha1dir://b1618868a12e92d8fb5df2b60b34dc0716a40552.manual_franklab/tetrode_2400s/sorter1_1`
- SYNTH_MEAREC_NEURONEXUS/synth_mearec_neuronexus_noise10_K10_C32/001_synth: `sha1dir://10b2e53b6b3aa0731b763db42daa692c4e1564b0.synth_mearec_neuronexus/datasets_noise10_K10_C32/001_synth`
- SYNTH_MEAREC_NEURONEXUS/synth_mearec_neuronexus_noise10_K20_C32/001_synth: `sha1dir://10b2e53b6b3aa0731b763db42daa692c4e1564b0.synth_mearec_neuronexus/datasets_noise10_K20_C32/001_synth`
- SYNTH_MEAREC_NEURONEXUS/synth_mearec_neuronexus_noise10_K40_C32/001_synth: `sha1dir://10b2e53b6b3aa0731b763db42daa692c4e1564b0.synth_mearec_neuronexus/datasets_noise10_K40_C32/001_synth`
- SYNTH_MEAREC_NEURONEXUS/synth_mearec_neuronexus_noise20_K10_C32/001_synth: `sha1dir://10b2e53b6b3aa0731b763db42daa692c4e1564b0.synth_mearec_neuronexus/datasets_noise20_K10_C32/001_synth`
- SYNTH_MEAREC_NEURONEXUS/synth_mearec_neuronexus_noise20_K20_C32/001_synth: `sha1dir://10b2e53b6b3aa0731b763db42daa692c4e1564b0.synth_mearec_neuronexus/datasets_noise20_K20_C32/001_synth`
- SYNTH_MEAREC_NEURONEXUS/synth_mearec_neuronexus_noise20_K40_C32/001_synth: `sha1dir://10b2e53b6b3aa0731b763db42daa692c4e1564b0.synth_mearec_neuronexus/datasets_noise20_K40_C32/001_synth`
- SYNTH_MEAREC_TETRODE/synth_mearec_tetrode_noise10_K10_C4/001_synth: `sha1dir://3ea5c9bd992de2d27402b2e83259c679d76e9319.synth_mearec_tetrode/datasets_noise10_K10_C4/001_synth`
- SYNTH_MEAREC_TETRODE/synth_mearec_tetrode_noise10_K20_C4/001_synth: `sha1dir://3ea5c9bd992de2d27402b2e83259c679d76e9319.synth_mearec_tetrode/datasets_noise10_K20_C4/001_synth`
- SYNTH_MEAREC_TETRODE/synth_mearec_tetrode_noise20_K10_C4/001_synth: `sha1dir://3ea5c9bd992de2d27402b2e83259c679d76e9319.synth_mearec_tetrode/datasets_noise20_K10_C4/001_synth`
- SYNTH_MEAREC_TETRODE/synth_mearec_tetrode_noise20_K20_C4/001_synth: `sha1dir://3ea5c9bd992de2d27402b2e83259c679d76e9319.synth_mearec_tetrode/datasets_noise20_K20_C4/001_synth`
- SYNTH_VISAPY/mea_c30/set1: `sha1dir://ed0fe4de4ef2c54b7c9de420c87f9df200721b24.synth_visapy/mea_c30/set1`
- HYBRID_JANELIA/hybrid_drift/rec_16c_1200s_11: `sha1dir://669fa96c8182ee7f4039174f0940e94fa8e98ef5.hybrid_janelia/drift/rec_16c_1200s_11`
- HYBRID_JANELIA/hybrid_static/rec_16c_1200s_11: `sha1dir://669fa96c8182ee7f4039174f0940e94fa8e98ef5.hybrid_janelia/static/rec_16c_1200s_11`
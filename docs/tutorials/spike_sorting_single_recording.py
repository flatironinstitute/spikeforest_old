#!/usr/bin/env python

import os
import shutil
from spikeforest import example_datasets
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor

recording, sorting_true = example_datasets.toy_example1() 

recdir = 'toy_example1'

# remove the toy recording directory if it exists
if os.path.exists(recdir):
    shutil.rmtree(recdir)

print('Preparing toy recording...')
SFMdaRecordingExtractor.write_recording(recording=recording, save_path=recdir)
SFMdaSortingExtractor.write_sorting(sorting=sorting_true, save_path=recdir + '/firings_true.mda')



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

# Now you may inspect test_outputs/comparison.html (in a browser)
# and test_outputs/true_units_info.json


print('Done. See outputs/')
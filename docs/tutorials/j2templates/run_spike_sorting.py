# import a spike sorter from the spikesorters module of spikeforest
from spikeforestsorters import MountainSort4
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
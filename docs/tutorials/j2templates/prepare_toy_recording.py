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


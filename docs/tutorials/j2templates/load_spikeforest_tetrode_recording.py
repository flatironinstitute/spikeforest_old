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
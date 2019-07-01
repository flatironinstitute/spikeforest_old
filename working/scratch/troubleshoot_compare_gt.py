from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
from mountaintools import client as mt

# Configure to download from the public spikeforest kachery node
mt.configDownloadFrom('spikeforest.public')

# Load the recording with its ground truth
recdir = 'sha1dir://be6ce9f60fe1963af235862dc8197c9753b4b6f5.hybrid_janelia/drift_siprobe/rec_16c_1200s_11'

print('Loading recording...')
recording = SFMdaRecordingExtractor(dataset_directory=recdir, download=True)
sorting_true = SFMdaSortingExtractor(firings_file=recdir + '/firings_true.mda')

sorting_ms4 = SFMdaSortingExtractor(firings_file='sha1://f1c6fdf52a2873d6f746e44dab6bf7ccd2937d97/f1c6fdf52a2873d6f746e44dab6bf7ccd2937d97/firings.mda')

# import from the spikeforest package
import spikeforest_analysis as sa

# write the ground truth firings file
SFMdaSortingExtractor.write_sorting(
    sorting=sorting_true,
    save_path='test_outputs/firings_true.mda'
)

# run the comparison
print('Compare with truth...')
import time
timer = time.time()

## Old method
sa.GenSortingComparisonTable.execute(
    firings='test_outputs/firings.mda',
    firings_true='test_outputs/firings_true.mda',
    units_true=[],  # use all units
    json_out='test_outputs/comparison_old.json',
    html_out='test_outputs/comparison_old.html',
    _container=None,
    _force_run=True
)
print('ELAPSED::::::::::::::: {}'.format(time.time()-timer))

# New method
timer = time.time()
sa.GenSortingComparisonTableNew.execute(
    firings='test_outputs/firings.mda',
    firings_true='test_outputs/firings_true.mda',
    units_true=[],  # use all units
    json_out='test_outputs/comparison_new.json',
    html_out='test_outputs/comparison_new.html',
    _container=None,
    _force_run=True
)
print('ELAPSED::::::::::::::: {}'.format(time.time()-timer))

# we may also want to compute the SNRs of the ground truth units
# together with firing rates and other information
print('Compute units info...')
sa.ComputeUnitsInfo.execute(
    recording_dir=recdir,
    firings='test_outputs/firings_true.mda',
    json_out='test_outputs/true_units_info.json'
)

import numpy as np

for suf in ['old', 'new']:
  print('----------------------------------------------------')
  print('RESULTS FOR {}'.format(suf))
  # Load and consolidate the outputs
  true_units_info = mt.loadObject(path='test_outputs/true_units_info.json')
  comparison = mt.loadObject(path='test_outputs/comparison_{}.json'.format(suf))
  true_units_info_by_unit_id = dict()
  for unit in true_units_info:
    true_units_info_by_unit_id[unit['unit_id']] = unit
  for unit in comparison.values():
    unit['true_unit_info'] = true_units_info_by_unit_id[unit['unit_id']]
    
  # # Print SNRs and accuracies
  # for unit in comparison.values():
  #   print('Unit {}: SNR={}, accuracy={}'.format(unit['unit_id'], unit['true_unit_info']['snr'], unit['accuracy']))
    
  # Report number of units found
  snrthresh = 8
  units_above = [unit for unit in comparison.values() if float(unit['true_unit_info']['snr'] > snrthresh)]
  print('Avg. accuracy for units with snr >= {}: {}'.format(snrthresh, np.mean([float(unit['accuracy']) for unit in units_above])))
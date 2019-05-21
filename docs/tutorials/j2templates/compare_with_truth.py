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

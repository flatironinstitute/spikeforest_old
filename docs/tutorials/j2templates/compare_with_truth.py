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

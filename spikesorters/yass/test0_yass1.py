# %% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
import os
try:
    os.chdir(os.path.join(os.getcwd(), 'working/spikeforest_test1'))
    print(os.getcwd())
except:
    pass

# %%
import spikeforest_analysis as sa
from cairio import client as ca
import os


# %%

def define_sorters():
    sorter_ms4_thr3 = dict(
        name='MountainSort4-thr3',
        processor_name='MountainSort4',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
            detect_threshold=3.1
        )
    )

    sorter_sc = dict(
        name='SpykingCircus',
        processor_name='SpykingCircus',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        )
    )

    sorter_yass = dict(
        name='yass',
        processor_name='yass',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        )
    )
    return [sorter_ms4_thr3, sorter_sc]


# %%
compute_resource = 'local-computer'

# Use this to control whether we force the processing to re-run (by default it uses cached results)
os.environ['MLPROCESSORS_FORCE_RUN'] = 'FALSE'  # FALSE or TRUE

# This is the id of the output -- for later retrieval by GUI's, etc
output_id = 'spikeforest_test1'

# Grab a couple recordings for testing
recording1 = dict(
    recording_name='001_synth',
    study_name='datasets_noise10_K10_C4-test',
    study_set='magland_synth-test',
    directory='kbucket://15734439d8cf/groundtruth/magland_synth/datasets_noise10_K10_C4/001_synth'
)
recording2 = dict(
    recording_name='002_synth',
    study_name='datasets_noise10_K10_C4-test',
    study_set='magland_synth-test',
    directory='kbucket://15734439d8cf/groundtruth/magland_synth/datasets_noise10_K10_C4/002_synth'
)
recordings = [recording1, recording2]

# Summarize the recordings
recordings_B = sa.summarize_recordings(
    recordings=recordings, compute_resource=compute_resource)

# Sorters (algs and params) are defined below
sorters = define_sorters()

# We will be assembling the sorting results here
sorting_results = []

for sorter in sorters:
    # Sort the recordings
    sortings_A = sa.sort_recordings(
        sorter=sorter,
        recordings=recordings_B,
        compute_resource=compute_resource
    )

    # Summarize the sortings
    sortings_B = sa.summarize_sortings(
        sortings=sortings_A,
        compute_resource=compute_resource
    )

    # Compare with ground truth
    sortings_C = sa.compare_sortings_with_truth(
        sortings=sortings_B,
        compute_resource=compute_resource
    )

    # Append to results
    sorting_results = sorting_results+sortings_C

# TODO: collect all the units for aggregated analysis

# Save the output
print('Saving the output')
ca.saveObject(
    key=dict(
        name='spikeforest_results',
        output_id=output_id
    ),
    object=dict(
        recordings=recordings_B,
        sorting_results=sorting_results
    )
)

# %%

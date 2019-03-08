#!/usr/bin/env python

import spikeforest_analysis as sa
from cairio import client as ca
from spikeforest import spikeextractors as se
import os
import shutil

# This file runs a spikeforest processing pipeline locally (no internet connection, except for downloading singularity containers if needed)
#    * Generate synthetic recordings (toy recordings)
#    * Summarize the recordings
#    * Sort the recordings
#    * Summarize the sortings
#    * Compare with ground truth
#    * Save results to kbucket (local) for later retrieval by GUIs, website, etc
#
#    NOTE: For now the singularity containers need to be on your system --
#          will improve this functionality in the future
#
#    Modify the settings below and then run this file using python 3


def main():
    # generate toy recordings
    delete_recordings = False
    num_recordings = 1
    for num in range(1, num_recordings+1):
        name = 'toy_example{}'.format(num)
        if delete_recordings:
            if os.path.exists(name):
                shutil.rmtree(name)
        if not os.path.exists(name):
            rx, sx_true = se.example_datasets.toy_example1(
                duration=60, num_channels=4, samplerate=30000, K=10)
            se.MdaRecordingExtractor.writeRecording(
                recording=rx, save_path=name)
            se.MdaSortingExtractor.writeSorting(
                sorting=sx_true, save_path=name+'/firings_true.mda')

    # Use this to optionally connect to a kbucket share:
    # ca.autoConfig(collection='spikeforest',key='spikeforest2-readwrite',ask_password=True)
    # for downloading containers if needed
    ca.setRemoteConfig(alternate_share_ids=['spikeforest.spikeforest2'])

    # Specify the compute resource (see the note above)
    compute_resource = None

    # Use this to control whether we force the processing to re-run (by default it uses cached results)
    os.environ['MLPROCESSORS_FORCE_RUN'] = 'FALSE'  # FALSE or TRUE

    # This is the id of the output -- for later retrieval by GUI's, etc
    output_id = 'spikeforest_test0'

    # Grab the recordings for testing
    recordings = [
        dict(
            recording_name='toy_example{}'.format(num),
            study_name='toy_examples',
            directory=os.path.abspath('toy_example{}'.format(num))
        )
        for num in range(1, num_recordings+1)
    ]

    studies = [
        dict(
            name='toy_examples',
            study_set='toy_examples',
            directory=os.path.abspath('.'),
            description='Toy examples.'
        )
    ]

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
            studies=studies,
            recordings=recordings_B,
            sorting_results=sorting_results
        )
    )


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
        name='Yass',
        processor_name='Yass',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        )
    )
    sorter_ks = dict(
        name='KiloSort',
        processor_name='KiloSort',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        )
    )
    # return [sorter_ms4_thr3, sorter_sc, sorter_yass]
    return [sorter_ks]


if __name__ == "__main__":
    main()

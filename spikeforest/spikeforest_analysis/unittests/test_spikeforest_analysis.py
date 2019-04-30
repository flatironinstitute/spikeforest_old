#!/usr/bin/env python

import spikeforest_analysis as sa
from mountaintools import client as mt
from spikeforest import example_datasets
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
import os
import shutil
import sfdata as sf
import numpy as np
import pytest

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


@pytest.mark.slow
@pytest.mark.analysis
def test_spikeforest_analysis(tmpdir):
    tmpdir = str(tmpdir)

    # generate toy recordings
    delete_recordings = True
    num_recordings = 2
    duration = 15
    for num in range(1, num_recordings+1):
        dirname = tmpdir+'/toy_example{}'.format(num)
        if delete_recordings:
            if os.path.exists(dirname):
                shutil.rmtree(dirname)
        if not os.path.exists(dirname):
            rx, sx_true = example_datasets.toy_example1(
                duration=duration, num_channels=4, samplerate=30000, K=10)
            SFMdaRecordingExtractor.writeRecording(
                recording=rx, save_path=dirname)
            SFMdaSortingExtractor.writeSorting(
                sorting=sx_true, save_path=dirname+'/firings_true.mda')

    # # Use this to optionally connect to a kbucket share:
    # # ca.autoConfig(collection='spikeforest',key='spikeforest2-readwrite',ask_password=True)
    # # for downloading containers if needed
    mt.configDownloadFrom(['spikeforest.spikeforest2'])

    # Specify the compute resource (see the note above)
    # compute_resource = 'local-computer'
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
            directory=tmpdir+'/toy_example{}'.format(num)
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
    recordings = sa.summarize_recordings(
        recordings=recordings, compute_resource=compute_resource)

    # Sorters (algs and params) are defined below
    sorters = _define_sorters()

    # We will be assembling the sorting results here
    sorting_results = []

    for sorter in sorters:
        # Sort the recordings
        sortings = sa.sort_recordings(
            sorter=sorter,
            recordings=recordings,
            compute_resource=compute_resource
        )

        # Summarize the sortings
        sortings = sa.summarize_sortings(
            sortings=sortings,
            compute_resource=compute_resource
        )

        # Compare with ground truth
        sortings = sa.compare_sortings_with_truth(
            sortings=sortings,
            compute_resource=compute_resource
        )

        # Append to results
        sorting_results = sorting_results+sortings

    # TODO: collect all the units for aggregated analysis

    aggregated_sorting_results = sa.aggregate_sorting_results(studies, recordings, sorting_results)

    # Save the output
    print('Saving the output')
    mt.saveObject(
        key=dict(
            name='spikeforest_results',
            output_id=output_id
        ),
        object=dict(
            studies=studies,
            recordings=recordings,
            sorting_results=sorting_results,
            aggregated_sorting_results=mt.saveObject(object=aggregated_sorting_results)
        )
    )

    for sr in aggregated_sorting_results['study_sorting_results']:
        study_name=sr['study']
        sorter_name=sr['sorter']
        n1=np.array(sr['num_matches'])
        n2=np.array(sr['num_false_positives'])
        n3=np.array(sr['num_false_negatives'])
        accuracies=n1/(n1+n2+n3)
        avg_accuracy=np.mean(accuracies)
        txt='STUDY: {}, SORTER: {}, AVG ACCURACY: {}'.format(study_name,sorter_name,avg_accuracy)
        print(txt)
        if avg_accuracy<0.3:
            if sorter_name == 'Yass':
                print('Average accuracy is too low, but we are excusing Yass for now.')
            else:
                raise Exception('Average accuracy is too low for test----- '+txt)


def _define_sorters():
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
    return [sorter_ms4_thr3, sorter_sc, sorter_yass]
    # return [sorter_ms4_thr3]

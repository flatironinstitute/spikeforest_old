#!/usr/bin/env python

import spikeforest_analysis as sa
from mountaintools import client as mt
from spikeforest import spikeextractors as se
import os
import shutil
import sfdata as sf
import numpy as np
import mlprocessors as mlpr


def main():
    mt.login(ask_password=True)
    mt.configRemoteReadWrite(collection='spikeforest',share_id='spikeforest.spikeforest2')

    # Use this to optionally connect to a kbucket share:
    # for downloading containers if needed
    # (in the future we will not need this)
    mt.setRemoteConfig(alternate_share_ids=['spikeforest.spikeforest2'])
    mlpr.configComputeResource('default', resource_name='ccmlin008-80',collection='spikeforest',share_id='spikeforest.spikeforest2')
    mlpr.configComputeResource('ks', resource_name='ccmlin008-80',collection='spikeforest',share_id='spikeforest.spikeforest2')

    # Use this to control whether we force the processing to run (by default it uses cached results)
    os.environ['MLPROCESSORS_FORCE_RUN'] = 'FALSE'  # FALSE or TRUE

    # This is the id of the output -- for later retrieval by GUI's, etc
    output_id = 'mearec_neuronexus'

    # Grab the recordings for testing
    group_name = 'mearec_neuronexus'

    a = mt.loadObject(
        key=dict(name='spikeforest_recording_group', group_name=group_name))

    recordings = a['recordings']
    studies = a['studies']

    #recordings=recordings[0:2]
    #studies=studies[0:1]

    # recordings = [recordings[0]]

    # Summarize the recordings
    recordings = sa.summarize_recordings(
        recordings=recordings, compute_resource='default')

    # Sorters (algs and params) are defined below
    sorters = _define_sorters()

    # We will be assembling the sorting results here
    sorting_results = []

    for sorter in sorters:
        # Sort the recordings
        compute_resource0 = 'default'
        if sorter['name'] == 'KiloSort':
            compute_resource0 = 'ks'
        sortings = sa.sort_recordings(
            sorter=sorter,
            recordings=recordings,
            compute_resource=compute_resource0
        )

        # Append to results
        sorting_results = sorting_results+sortings

    # Summarize the sortings
    sorting_results = sa.summarize_sortings(
        sortings=sorting_results,
        compute_resource='default'
    )

    # Compare with ground truth
    sorting_results = sa.compare_sortings_with_truth(
        sortings=sorting_results,
        compute_resource='default'
    )

    # Aggregate the results
    aggregated_sorting_results = sa.aggregate_sorting_results(
         studies, recordings, sorting_results)

    # Save the output
    print('Saving the output')
    mt.saveObject(
        key=dict(
            name='spikeforest_results'
        ),
        subkey=output_id,
        object=dict(
            studies=studies,
            recordings=recordings,
            sorting_results=sorting_results,
            aggregated_sorting_results=mt.saveObject(
                object=aggregated_sorting_results)
        )
    )

    for sr in aggregated_sorting_results['study_sorting_results']:
        study_name = sr['study']
        sorter_name = sr['sorter']
        n1 = np.array(sr['num_matches'])
        n2 = np.array(sr['num_false_positives'])
        n3 = np.array(sr['num_false_negatives'])
        accuracies = n1/(n1+n2+n3)
        avg_accuracy = np.mean(accuracies)
        txt = 'STUDY: {}, SORTER: {}, AVG ACCURACY: {}'.format(
            study_name, sorter_name, avg_accuracy)
        print(txt)

def _define_sorters():
    sorter_ms4_thr3 = dict(
        name='MountainSort4-thr3',
        processor_name='MountainSort4',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
            detect_threshold=3
        )
    )

    def sorter_irc_template(prm_template_name, detect_threshold=5):
        sorter_irc = dict(
            name='IronClust-{}'.format(prm_template_name),
            processor_name='IronClust',
            params=dict(
                detect_sign=-1,
                adjacency_radius=50,
                prm_template_name="{}_template.prm".format(prm_template_name),
                detect_threshold=detect_threshold
            )
        )
        return sorter_irc

    #sorter_irc_tetrode = sorter_irc_template('tetrode')
    #sorter_irc_drift = sorter_irc_template('drift')
    sorter_irc_static = sorter_irc_template('static')

    sorter_sc = dict(
        name='SpykingCircus',
        processor_name='SpykingCircus',
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

    sorter_yass = dict(
        name='Yass',
        processor_name='Yass',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        )
    )

    return [sorter_ms4_thr3, sorter_sc, sorter_yass, sorter_irc_static]


if __name__ == "__main__":
    main()

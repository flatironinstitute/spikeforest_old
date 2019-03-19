#!/usr/bin/env python

import spikeforest_analysis as sa
from mountaintools import client as mt
from spikeforest import spikeextractors as se
import os, sys
import shutil
import sfdata as sf
import numpy as np
import mlprocessors as mlpr


def main():
    resource_name1 = 'ccmlin008-parallel'
    resource_name2 = 'ccmlin008-parallel'
    if len(sys.argv)>1:
        resource_name1 = sys.argv[1]
    if len(sys.argv)>2:
        resource_name2 = sys.argv[2]
    print('Compute resources used:')
    print('  resource_name1 (srun CPU): ', resource_name1)
    print('  resource_name2 (Local GPU): ', resource_name2)    
    mt.login(ask_password=True)
    mt.configRemoteReadWrite(collection='spikeforest',share_id='spikeforest.spikeforest2')
    mt.setRemoteConfig(alternate_share_ids=['spikeforest.spikeforest2'])
    mlpr.configComputeResource('default', resource_name=resource_name1,collection='spikeforest',share_id='spikeforest.spikeforest2')
    mlpr.configComputeResource('gpu', resource_name=resource_name2,collection='spikeforest',share_id='spikeforest.spikeforest2')

    # Use this to control whether we force the processing to run (by default it uses cached results)
    os.environ['MLPROCESSORS_FORCE_RUN'] = 'FALSE'  # FALSE or TRUE

    # This is the id of the output -- for later retrieval by GUI's, etc
    output_id = 'magland_synth_test'

    # Grab the recordings for testing
    group_name = 'magland_synth_test'

    a = mt.loadObject(
        key=dict(name='spikeforest_recording_group', group_name=group_name))

    recordings = a['recordings']
    studies = a['studies']

    recordings=recordings[0:3]
    studies=studies[0:1]

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
        if 'KiloSort' in sorter['name'] or 'IronClust' in sorter['name']:
            compute_resource0 = 'gpu'
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

    sorter_irc_tetrode = dict(
        name='IronClust-tetrode',
        processor_name='IronClust',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
            detect_threshold=5,
            prm_template_name="tetrode_template.prm"
        )
    )

    sorter_irc_drift = dict(
        name='IronClust-drift',
        processor_name='IronClust',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
            prm_template_name="drift_template.prm"
        )
    )

    sorter_irc_static = dict(
        name='IronClust-static',
        processor_name='IronClust',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
            detect_threshold=4,
            prm_template_name="static_template.prm"
        )
    )

    def sorter_irc_template(prm_template_name):
        sorter_irc = dict(
            name='IronClust-{}'.format(prm_template_name),
            processor_name='IronClust',
            params=dict(
                detect_sign=-1,
                adjacency_radius=50,
                prm_template_name="{}_template.prm".format(prm_template_name)
            )
        )
        return sorter_irc

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

    sorter_ks2 = dict(
        name='KiloSort2',
        processor_name='KiloSort2',
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

    sorter_ms4_error = dict(
        name='MountainSort4-error',
        processor_name='MountainSort4TestError',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
            detect_threshold=3,
            throw_error=True
        )
    )

    # return [sorter_ms4_thr3, sorter_sc, sorter_irc_tetrode, sorter_ks]
    # return [sorter_ms4_thr3, sorter_sc, sorter_irc_tetrode, sorter_ks, sorter_yass]
    # return [sorter_ms4_thr3, sorter_sc, sorter_irc_static, sorter_yass, sorter_ks]
    # return [sorter_yass]
    return [sorter_ms4_error, sorter_sc]


if __name__ == "__main__":
    main()
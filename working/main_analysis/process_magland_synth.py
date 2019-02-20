#!/usr/bin/env python

import spikeforest_analysis as sa
from cairio import client as ca
import spikeextractors as se
import os
import shutil
import spikeforest as sf
import numpy as np
import pytest


def main():
    ca.autoConfig(collection='spikeforest',
                  key='spikeforest2-readwrite', ask_password=True)

    # Use this to optionally connect to a kbucket share:
    # for downloading containers if needed
    ca.setRemoteConfig(alternate_share_ids=['69432e9201d0'])

    # Specify the compute resource (see the note above)
    # compute_resource = 'local-computer'
    compute_resource = None

    # Use this to control whether we force the processing to re-run (by default it uses cached results)
    os.environ['MLPROCESSORS_FORCE_RUN'] = 'FALSE'  # FALSE or TRUE

    # This is the id of the output -- for later retrieval by GUI's, etc
    output_id = 'spikeforest_magland_synth'

    # Grab the recordings for testing
    group_name = 'magland_synth_test'

    a = ca.loadObject(
        key=dict(name='spikeforest_recording_group', group_name=group_name))

    recordings = a['recordings']
    studies = a['studies']

    recordings = [recordings[0]]

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

    compiled_sorting_results = sa.compile_sorting_results(
        studies, recordings, sorting_results)

    # Save the output
    print('Saving the output')
    ca.saveObject(
        key=dict(
            name='spikeforest_results',
            output_id=output_id
        ),
        object=dict(
            studies=studies,
            recordings=recordings,
            sorting_results=sorting_results,
            compiled_sorting_results=ca.saveObject(
                object=compiled_sorting_results)
        )
    )

    for sr in compiled_sorting_results['study_sorting_results']:
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
    # return [sorter_ms4_thr3, sorter_sc, sorter_irc_tetrode, sorter_ks]
    # return [sorter_ms4_thr3, sorter_sc, sorter_irc_tetrode]
    return [sorter_ms4_thr3]


if __name__ == "__main__":
    main()

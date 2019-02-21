#!/usr/bin/env python

import spikeforest_analysis as sa
from cairio import client as ca
import os

# This file runs a spikeforest processing pipeline with the following steps:
#    * Attach to the desire kbucket share and compute resources
#    * Collect recordings and sorters
#    * Summarize the recordings
#    * Sort the recordings
#    * Summarize the sortings
#    * Compare with ground truth
#    * Save results to kbucket for later retrieval by GUIs, website, etc
#
#    NOTE: the required singularity containers for running all processing
#          will automatically be downloaded to the compute resource.
#          If you are using your local machine as compute resource (see below),
#          this may take some time depending on your internet connection.
#          Downloaded containers are cached so they only need to be downloaded
#          once.
#
# Usage:
#
#    First make sure that your compute resource is set up and listening.
#    If you want to just use your local machine, you can either
#    set `compute_resource=None` below or use the preferred method of
#    listening on your local machine as 'local-computer'. Note that if you
#    want to use a remote resource, then you will need to connect to the
#    appropriate kbucket share with read/write privileges. See docs (in progress)
#    for more information.
#
#    Modify the settings below and then run this file using python


def main():
    # Use this to optionally connect to a kbucket share:
    ca.autoConfig(collection='spikeforest', key='spikeforest2-readwrite',
                  ask_password=True, password=os.environ.get('SPIKEFOREST_PASSWORD', None))

    # Specify the compute resource (see the note above)
    compute_resource = 'ccmlin008-80'
    compute_resource_ks = 'ccmlin008-kilosort'

    # Use this to control whether we force the processing to re-run (by default it uses cached results)
    os.environ['MLPROCESSORS_FORCE_RUN'] = 'FALSE'  # FALSE or TRUE

    # This is the id of the output -- for later retrieval by GUI's, etc
    output_id = 'spikeforest_test2'

    #group_name = 'magland_synth_test'
    group_name = 'magland_synth'

    a = ca.loadObject(
        key=dict(name='spikeforest_recording_group', group_name=group_name))

    recordings = a['recordings']
    studies = a['studies']

    # Summarize the recordings
    recordings_B = sa.summarize_recordings(
        recordings=recordings, compute_resource=compute_resource)

    # Sorters (algs and params) are defined below
    sorters = define_sorters()

    # We will be assembling the sorting results here
    sorting_results_A = []

    for sorter in sorters:
        # Sort the recordings
        compute_resource0 = compute_resource
        if sorter['name'] == 'KiloSort':
            compute_resource0 = compute_resource_ks
        sortings = sa.sort_recordings(
            sorter=sorter,
            recordings=recordings_B,
            compute_resource=compute_resource0
        )

        # Append to results
        sorting_results_A = sorting_results_A+sortings

    # Summarize the sortings
    sorting_results_B = sa.summarize_sortings(
        sortings=sorting_results_A,
        compute_resource=compute_resource
    )

    # Compare with ground truth
    sorting_results_C = sa.compare_sortings_with_truth(
        sortings=sorting_results_B,
        compute_resource=compute_resource
    )

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
            sorting_results=sorting_results_C
        )
    )


def define_sorters():
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
    return [sorter_ms4_thr3, sorter_sc, sorter_irc_tetrode]


if __name__ == "__main__":
    main()

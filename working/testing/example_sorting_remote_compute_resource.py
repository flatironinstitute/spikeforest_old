#!/usr/bin/env python

# IMPORTANT: This requires that the ccmlin008-test compute resource is running
# and that you have access to the appropriate resources via login user

import spikeforest_analysis as sa
from mountaintools import client as mt
from spikeforest import spikeextractors as se
import os
import shutil
import sfdata as sf
import numpy as np
import pytest


def main():
    # log in and connect to a remote collection/share
    # You can store credentials in ~/.mountaintools/.env
    # (see example_login.py for more info)
    mt.login(interactive=True)
    mt.configRemoteReadWrite(collection='spikeforest',share_id='spikeforest.spikeforest2')

    # specify the compute resource
    compute_resource=dict(
        resource_name='ccmlin008-test',
        collection='spikeforest',
        share_id='69432e9201d0'
    )

    # location of recordings on kbucket
    recordings_dir='kbucket://15734439d8cf/testing/toy_recordings'

    # for downloading containers if needed
    mt.setRemoteConfig(alternate_share_ids=['spikeforest.spikeforest2'])

    # Use this to control whether we force the processing to re-run (by default it uses cached results)
    os.environ['MLPROCESSORS_FORCE_RUN'] = 'FALSE'  # FALSE or TRUE

    # This is the id of the output -- for later retrieval by GUI's, etc
    output_id = 'toy_example_remote_compute_resource'

    # Grab the recordings for testing
    recordings = [
        dict(
            name='example1',
            study='toy_examples_remote_compute_resource',
            directory=os.path.join(recordings_dir, 'example1')
        )
    ]

    recordings = recordings*3

    studies = [
        dict(
            name='toy_examples_remote_compute_resource',
            study_set='toy_examples',
            directory=recordings_dir,
            description='Toy examples for remote processing.'
        )
    ]

    # Summarize the recordings
    print('>>>>>>> Summarize recordings...')
    recordings = sa.summarize_recordings(
        recordings=recordings, compute_resource=compute_resource)

    # Sorters (algs and params) are defined below
    sorters = _define_sorters()

    # We will be assembling the sorting results here
    sorting_results = []

    for sorter in sorters:
        # Sort the recordings
        compute_resource0=compute_resource
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
        compute_resource=compute_resource
    )

    # Compare with ground truth
    sorting_results = sa.compare_sortings_with_truth(
        sortings=sorting_results,
        compute_resource=compute_resource
    )

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
            sorting_results=sorting_results
        )
    )


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
    # return [sorter_ms4_thr3, sorter_sc, sorter_irc_static]
    # return [sorter_ms4_thr3, sorter_sc, sorter_irc_static]
    return [sorter_ms4_thr3, sorter_irc_static]


if __name__ == "__main__":
    main()

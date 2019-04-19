#!/usr/bin/env python

from mountaintools import client as mt
import os, sys
import mlprocessors as mlpr
import mtlogging

from apply_sorters_to_recordings import apply_sorters_to_recordings


@mtlogging.log(root=True)
def main():
    resource_name1 = 'ccmlin008-80'
    resource_name2 = 'ccmlin008-gpu'
    if len(sys.argv)>1:
        resource_name1 = sys.argv[1]
    if len(sys.argv)>2:
        resource_name2 = sys.argv[2]
    print('Compute resources used:')
    print('  resource_name1 (srun CPU): ', resource_name1)
    print('  resource_name2 (Local GPU): ', resource_name2)

    mt.login(ask_password=True)
    mt.configRemoteReadWrite(collection='spikeforest',share_id='spikeforest.spikeforest2')

    mt.configDownloadFrom(['spikeforest.spikeforest2'])

    mlpr.configComputeResource('default', resource_name=resource_name1, collection='spikeforest', share_id='spikeforest.spikeforest2')
    mlpr.configComputeResource('gpu', resource_name=resource_name2, collection='spikeforest', share_id='spikeforest.spikeforest2')

    # Use this to control whether we force the processing to run (by default it uses cached results)
    os.environ['MLPROCESSORS_FORCE_RUN'] = 'FALSE'  # FALSE or TRUE

    # This is the id of the output -- for later retrieval by GUI's, etc
    output_id = 'mearec_neuronexus'

    # Grab the recordings
    recording_group_name = 'mearec_neuronexus'
    a = mt.loadObject(
        key=dict(name='spikeforest_recording_group', group_name=recording_group_name))

    recordings = a['recordings']
    studies = a['studies']

    sorters = _define_sorters()

    apply_sorters_to_recordings(sorters=sorters, recordings=recordings, studies=studies, output_id=output_id)

def _define_sorters():
    sorter_ms4_thr3 = dict(
        name='MountainSort4-thr3',
        processor_name='MountainSort4',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
            detect_threshold=3
        ),
        compute_resource='default'
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
            ),
            compute_resource='gpu'
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
        ),
        compute_resource='default'
    )

    sorter_ks = dict(
        name='KiloSort',
        processor_name='KiloSort',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        ),
        compute_resource='gpu'
    )

    sorter_yass = dict(
        name='Yass',
        processor_name='Yass',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
        ),
        compute_resource='default'
    )

    return [sorter_ms4_thr3, sorter_sc, sorter_yass, sorter_irc_static, sorter_ks]


if __name__ == "__main__":
    main()

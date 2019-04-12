#!/usr/bin/env python

from mountaintools import client as mt
import os, sys
import mlprocessors as mlpr
import mtlogging
import argparse

from apply_sorters_to_recordings import apply_sorters_to_recordings


@mtlogging.log(root=True)
def main():

    parser = argparse.ArgumentParser(description = 'Run a SpikeForest analysis')
    parser.add_argument('--recording_group',help='Name of recording group', required=True)
    parser.add_argument('--output_id',help='ID of the output', required=True)
    parser.add_argument('--compute_resource_default',help='Name of default compute resource', required=False, default=None)
    parser.add_argument('--compute_resource_gpu',help='Name of compute resource for gpu', required=False, default=None)
    parser.add_argument('--collection',help='Name of collection to connect to', required=False, default=None)
    parser.add_argument('--share_id',help='Name of kbucket share id to connect to', required=False, default=None)
    parser.add_argument('--sorter_codes',help='Comma-separated codes of sorters to run', required=False, default='ms4,irc,sc,yass')
    parser.add_argument('--job_timeout',help='Number of seconds before timeing out a sorting job', required=False, default=60*20)
    parser.add_argument('--test', help='Only run a few, and prepend test_ to the output', action='store_true')

    args = parser.parse_args()

    print(args)

    if args.collection:
        mt.login(ask_password=True)
        mt.configRemoteReadWrite(collection=args.collection,share_id=args.share_id)

    # mt.setRemoteConfig(alternate_share_ids=['spikeforest.spikeforest2'])

    mlpr.configComputeResource('default', resource_name=args.compute_resource_default, collection=args.collection, share_id=args.share_id)
    mlpr.configComputeResource('gpu', resource_name=args.compute_resource_gpu, collection=args.collection, share_id=args.share_id)

    # This is the id of the output -- for later retrieval by GUI's, etc
    output_id = args.output_id

    # Grab the recordings
    recording_group_name = args.recording_group
    a = mt.loadObject(
        key=dict(name='spikeforest_recording_groups'),
        subkey=recording_group_name
    )
    if a is None:
        # revert to old method
        a = mt.loadObject(
            key=dict(name='spikeforest_recording_group', group_name=recording_group_name))
        if a is not None:
            print('WARNING! Reverting to old method of getting the recording group. Please update your recording groups!')
    if a is None:
        raise Exception('Unable to find data for recording group: '+recording_group_name)

    recordings = a['recordings']
    studies = a['studies']

    if args.test:
        output_id = 'test_'+output_id
        recordings=recordings[0:2]
        studies=studies[0:1]

    sorters = _define_sorters()
    sorter_codes=list(args.sorter_codes.split(','))
    sorters = [sorter for sorter in sorters if sorter['code'] in sorter_codes]
    print('Using sorters: ',[sorter['name'] for sorter in sorters])

    apply_sorters_to_recordings(sorters=sorters, recordings=recordings, studies=studies, output_id=output_id, job_timeout=float(args.job_timeout))

def _define_sorters():
    sorter_ms4_thr3 = dict(
        code='ms4',
        name='MountainSort4-thr3',
        processor_name='MountainSort4',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
            detect_threshold=3
        ),
        compute_resource='default'
    )

    def sorter_irc_template(prm_template_name, code, detect_threshold=4.5):
        sorter_irc = dict(
            code=code,
            name='IronClust-{}'.format(prm_template_name),
            processor_name='IronClust',
            params=dict(
                detect_sign=-1,
                prm_template_name="{}_template.prm".format(prm_template_name),
            ),
            compute_resource='gpu'
        )
        return sorter_irc

    #sorter_irc_tetrode = sorter_irc_template('tetrode')
    #sorter_irc_drift = sorter_irc_template('drift')
    sorter_irc_static = sorter_irc_template('static', 'irc')
    sorter_irc_drift2 = sorter_irc_template('drift2', 'irc-d2')

    sorter_sc = dict(
        code='sc',
        name='SpykingCircus',
        processor_name='SpykingCircus',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        ),
        compute_resource='default'
    )

    sorter_ks = dict(
        code='ks',
        name='KiloSort',
        processor_name='KiloSort',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        ),
        compute_resource='gpu'
    )

    sorter_ks2 = dict(
        code='ks2',
        name='KiloSort2',
        processor_name='KiloSort2',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50
        ),
        compute_resource='gpu'
    )    

    sorter_yass = dict(
        code='yass',
        name='Yass',
        processor_name='Yass',
        params=dict(
            detect_sign=-1,
            adjacency_radius=50,
        ),
        compute_resource='default'
    )

    return [sorter_ms4_thr3, sorter_sc, sorter_yass, sorter_irc_static, sorter_irc_drift2, sorter_ks, sorter_ks2]


if __name__ == "__main__":
    main()

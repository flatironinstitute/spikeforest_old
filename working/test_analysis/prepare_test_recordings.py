#!/usr/bin/env python

from mountaintools import client as mt

mt.configDownloadFrom('spikeforest.kbucket')


def do_prepare(recording_group, study_name):
    print(recording_group, study_name)
    X = mt.loadObject(path="key://pairio/spikeforest/spikeforest_recording_group.{}.json".format(recording_group))
    studies = [y for y in X['studies'] if (y['name'] == study_name)]
    recordings = [y for y in X['recordings'] if y['study'] == study_name]
    recordings = recordings[0:1]
    study_sets = X['study_sets']

    Y = dict(
        studies=studies,
        recordings=recordings,
        study_sets=study_sets
    )
    address = mt.saveObject(object=Y)
    assert address is not None
    dest_path = 'key://pairio/spikeforest/spikeforest_recording_group.test_{}.json'.format(recording_group)
    print(dest_path)
    mt.createSnapshot(path=address, upload_to='spikeforest.kbucket', dest_path=dest_path)

do_prepare(recording_group='synth_magland', study_name='synth_magland_noise10_K10_C4')
do_prepare(recording_group='paired_mea64c', study_name='paired_mea64c')

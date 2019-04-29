#!/usr/bin/env python

from mountaintools import client as mt

mt.configDownloadFrom('spikeforest.kbucket')

X = mt.loadObject(path="key://pairio/spikeforest/spikeforest_recording_group.synth_magland.json")
study_name = "synth_magland_noise10_K10_C4"
studies = [y for y in X['studies'] if (y['name']==study_name)]
recordings = [y for y in X['recordings'] if y['study']==study_name]
recordings = recordings[0:1]
study_sets = X['study_sets']

Y = dict(
    studies=studies,
    recordings=recordings,
    study_sets=study_sets
)
address = mt.saveObject(object=Y)
assert address is not None
print(address)
mt.createSnapshot(path=address, upload_to='spikeforest.kbucket', dest_path='key://pairio/spikeforest/spikeforest_recording_group.test_synth_magland.json')

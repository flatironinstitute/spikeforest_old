#!/usr/bin/env python

from mountaintools import client as mt
mt.login()
mt.configRemoteReadWrite(collection='spikeforest',share_id='spikeforest.spikeforest2')
sha1_path = mt.saveFile('spyking_circus.simg')
print(sha1_path)

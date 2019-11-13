#!/usr/bin/env python

from mountaintools import client as mt

sha1_path = mt.saveFile('spikeforest_basic.simg')
print(sha1_path)
sha1_path = mt.saveFile('spikeforest_basic.simg', upload_to='spikeforest.public')
print(sha1_path)

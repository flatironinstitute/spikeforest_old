#!/usr/bin/env python

from mountaintools import client as mt

mt.login()
sha1_path = mt.saveFile('spikeforest_basic.simg', upload_to='spikeforest.spikeforest2')
print(sha1_path)

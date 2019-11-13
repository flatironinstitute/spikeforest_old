#!/usr/bin/env python

from mountaintools import client as mt

mt.login()
sha1_path = mt.saveFile('mountainsort4.simg', upload_to='spikeforest.kbucket')
print(sha1_path)

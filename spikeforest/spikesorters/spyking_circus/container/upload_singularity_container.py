#!/usr/bin/env python

from cairio import client as ca

ca.autoConfig(collection='spikeforest',
              key='spikeforest2-readwrite', ask_password=True)
sha1_path = ca.saveFile('spyking_circus.simg')
print(sha1_path)

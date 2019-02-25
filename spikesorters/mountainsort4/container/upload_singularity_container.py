#!/usr/bin/env python

from cairio import client as ca

ca.autoConfig(collection='spikeforest',
              key='spikeforest2-readwrite', ask_password=True)
sha1_path = ca.saveFile('mountainsort4.simg')
print(sha1_path)

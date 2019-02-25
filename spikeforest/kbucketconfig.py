from cairio import client as ca
from copy import deepcopy
import json

def setKBucketConfig(*,config=None,collection=None,key=None):
    ca.autoConfig(collection=collection,key=key)

def kbucketConfigLocal(write=True):
    ca.setRemoteConfig(collection='',token='',share_id='',upload_token='')

def kbucketConfigRemote(*,name='spikeforest1-readonly',collection='spikeforest'):
    setKBucketConfig(collection=collection,name=name)
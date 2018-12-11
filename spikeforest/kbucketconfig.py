from kbucket import client as kb
from pairio import client as pa
import getpass
from copy import deepcopy
import json

def setKBucketConfig(*,config=None,collection=None,key=None,verbose=False,return_config=False):
  if key:
    if config:
      raise Exception('Cannot specify both key and config')
    config=pa.getObject(collection=collection,key=key)
  pa.setConfig(
    collections=config['pairio']['collections'],
    user=config['pairio']['user'],
    token=config['pairio']['token'],
    read_local=config['pairio']['read_local'],
    write_local=config['pairio']['write_local'],
    read_remote=config['pairio']['read_remote'],
    write_remote=config['pairio']['write_remote']
  )
  kb.setConfig(
    share_ids=config['kbucket']['share_ids'],
    upload_share_id=config['kbucket']['upload_share_id'],
    upload_token=config['kbucket']['upload_token'],
    load_local=config['kbucket']['load_local'],
    load_remote=config['kbucket']['load_remote'],
    save_remote=config['kbucket']['save_remote']
  )
  if verbose:
    config_display=deepcopy(config)
    if config_display['pairio']['token']:
      config_display['pairio']['token']='************'
    if config_display['kbucket']['upload_token']:
      config_display['kbucket']['upload_token']='************'
    print ('Set config:')
    print (json.dumps(config_display,indent=2))
  if return_config:
    return config

def kbucketConfigLocal(write=True):
  pa.setConfig(
      collections=[],
      user='',
      token='',
      read_local=True,write_local=False,read_remote=False,write_remote=False
  )
  kb.setConfig(
      share_ids=[],
      upload_share_id='',
      upload_token='',
      load_local=True,load_remote=False,save_remote=False
  )
  if write:
    pa.setConfig(
        write_local=True,
    )

def kbucketConfigRemote(*,name='spikeforest1-readonly',collection='spikeforest',password=None,ask_password=False,verbose=False,return_config=False):
  if ask_password:
    password=getpass.getpass('Enter password: ')
    if not password:
      raise Exception('No password entered')

  key=dict(name=name)
  if password:
    key2=dict(key=key,password=password)
  else:
    key2=key

  return setKBucketConfig(collection=collection,key=key2,verbose=verbose,return_config=return_config)

def kbucketConfigRemoteOld(*,user='spikeforest',share_id='spikeforest.spikeforest2',password=None,write=False):
  pa.setConfig(
      collections=[user],
      user='',
      token='',
      read_local=False,write_local=False,read_remote=True,write_remote=False
  )
  kb.setConfig(
      share_ids=[share_id],
      upload_share_id='',
      upload_token='',
      load_local=True,load_remote=True,save_remote=False
  )
  if write:
    if password is None:
      password=getpass.getpass('Enter the spikeforest password (or leave blank for read-only)')
    if not password:
      return
    pa.setConfig(
        user=user,
        token=pa.get(collection='spikeforest',key=dict(name='pairio_token',user=user,password=password)),
        write_remote=True
    )
    kb.setConfig(
        upload_share_id=share_id,
        upload_token=pa.get(collection='spikeforest',key=dict(name='kbucket_token',share_id=share_id,password=password)),
        save_remote=True
    )
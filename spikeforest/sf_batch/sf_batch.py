import spikeforest as sf
from kbucket import client as kb
from pairio import client as pa
import json
import os
import random
import string
from .sf_summarize_recording import sf_summarize_recording
from .sf_sort_recording import sf_sort_recording

def login(config):
    password=os.environ.get('SPIKEFOREST_PASSWORD',None)
    if not password:
        raise Exception('Environment variable not set: SPIKEFOREST_PASSWORD')
    sf.kbucketConfigRemote(share_id=config['share_id'],write=True,password=os.environ['SPIKEFOREST_PASSWORD'])

def sf_batch_prepare(config,*,clear_all=False):
    login(config)
    study_obj=kb.loadObject(key=dict(name='spikeforest_recordings'))
    recordings=select_recordings(study_obj,config)
    sorters=config['sorters']
    
    clear_in_process_only=(not clear_all)
    for ds in recordings:
        print ('PREPARE: {}/{}'.format(ds['study'],ds['name']))
        print ('Downloading raw.mda')
        dsdir=ds['directory']
        kb.realizeFile(dsdir+'/raw.mda')
        
        if config.get('summarize_recordings',None):
            key=dict(
                name='summarize_recording',
                batch_name=config['name'],
                study_name=ds['study'],
                recording_name=ds['name']
            )
            clear_result_for_key(key=key,in_process_only=clear_in_process_only)
        
        for sorter in sorters:
            key=dict(
                name='sort_recording',
                batch_name=config['name'],
                study_name=ds['study'],
                recording_name=ds['name'],
                sorter_name=sorter['name'],
                sorter_params=sorter['params']
            )
            clear_result_for_key(key=key,in_process_only=clear_in_process_only)

def sf_batch_run(config):
    login(config)
    study_obj=kb.loadObject(key=dict(name='spikeforest_recordings'))
    recordings=select_recordings(study_obj,config)
    sorters=config['sorters']
    
    code=''.join(random.choice(string.ascii_uppercase) for x in range(10))
    for i,ds in enumerate(recordings):
        if config.get('summarize_recordings',None):
            key=dict(
                name='summarize_recording',
                batch_name=config['name'],
                study_name=ds['study'],
                recording_name=ds['name']
            )
            if acquire_lock_for_key(key=key,code=code):
                try:
                    print ('========= Summarizing recording {}/{}: {}/{}'.format(i,len(recordings),ds['study'],ds['name']))
                    result0=sf_summarize_recording(ds)
                except:
                    if check_consistent_code(key=key,code=code):
                        pa.set(key=key,value='error-'+code)
                    raise
                if check_consistent_code(key=key,code=code):
                    kb.saveObject(key=key,object=result0)
                else:
                    print ('Warning: inconsistent code for {}'.format(json.dumps(key)))

        for sorter in sorters:
            key=dict(
                name='sort_recording',
                batch_name=config['name'],
                study_name=ds['study'],
                recording_name=ds['name'],
                sorter_name=sorter['name'],
                sorter_params=sorter['params']
            )
            if acquire_lock_for_key(key=key,code=code):
                try:
                    print ('========= Sorting recording {}/{}: {} - {}/{}'.format(i,len(recordings),sorter['name'],ds['study'],ds['name']))
                    result0=sf_sort_recording(sorter,ds)
                except:
                    if check_consistent_code(key=key,code=code):
                        pa.set(key=key,value='error-'+code)
                    raise
                if check_consistent_code(key=key,code=code):
                    kb.saveObject(key=key,object=result0)
                else:
                    print ('Warning: inconsistent code for {}'.format(json.dumps(key)))
                
def sf_batch_assemble(config):
    login(config)
    study_obj=kb.loadObject(key=dict(name='spikeforest_recordings'))
    recordings=select_recordings(study_obj,config)
    sorters=config['sorters']
    
    batch_output=dict(
        recordings=recordings,
        sorters=sorters,
        summarize_recording_results=[],
        sorting_results=[]
    )
    for ds in recordings:
        if config.get('summarize_recordings',None):
            print ('ASSEMBLE: {}/{}'.format(ds['study'],ds['name']))
            key=dict(
                name='summarize_recording',
                batch_name=config['name'],
                study_name=ds['study'],
                recording_name=ds['name']
            )
            result0=kb.loadObject(key=key)
            if not result0:
                raise Exception('Problem loading summarize_recording result {}'.format(json.dumps(key)))
            batch_output['summarize_recording_results'].append(result0)

        for sorter in sorters:
            print ('ASSEMBLE: {} {}/{}'.format(sorter['name'],ds['study'],ds['name']))
            key=dict(
                name='sort_recording',
                batch_name=config['name'],
                study_name=ds['study'],
                recording_name=ds['name'],
                sorter_name=sorter['name'],
                sorter_params=sorter['params']
            )
            result0=kb.loadObject(key=key)
            if not result0:
                raise Exception('Problem loading sort_recording result {}'.format(json.dumps(key)))
            batch_output['sorting_results'].append(result0)
            
    kb.saveObject(
        key=dict(
            batch_name=config['name'],
        ),
        object=batch_output
    )


def select_recordings(study_obj,config):
    recordings=[]
    for ds in study_obj['recordings']:
        if (not config['studies']) or (ds['study'] in config['studies']):
            if (not config['recordings']) or (ds['name'] in config['recordings']):
                recordings.append(ds)
    return recordings

def clear_result_for_key(*,key,in_process_only=False):
    val=pa.get(key=key)
    if val:
        if in_process_only:
            do_clear=((val.startswith('in-process')) or (val.startswith('error')))
        else:
            do_clear=True
        if do_clear:
            print ('Clearing results for: {}'+json.dumps(key))
            pa.set(key=key,value=None)

def acquire_lock_for_key(*,key,code):
    val=pa.get(key=key)
    if val:
        if val.startswith('in-process'):
            return False
        if val.startswith('error'):
            return False
        return False
    if not pa.set(key,'in-process-'+code,overwrite=False):
        return False
    return True

def check_consistent_code(*,key,code):
    val=pa.get(key=key)
    if not val:
        return False
    return (val=='in-process-'+code)
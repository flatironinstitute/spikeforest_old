import random
import string
from kbucket import client as kb
from pairio import client as pa
from .sf_sort_recording import sf_sort_recording
from .sf_summarize_recording import sf_summarize_recording

def clear_job_results(*,batch_name,incomplete_only=True):
  batch=kb.loadObject(key=dict(batch_name=batch_name))
  jobs=batch['jobs']
  for job in jobs:
    clear_job_result(job,incomplete_only=incomplete_only)

def download_recordings(*,batch_name):
  batch=kb.loadObject(key=dict(batch_name=batch_name))
  jobs=batch['jobs']
  for job in jobs:
    print('DOWNLOADING: '+job['label'])
    dsdir=job['recording']['directory']
    kb.realizeFile(dsdir+'/raw.mda')
    
def run_jobs(*,batch_name):
  batch=kb.loadObject(key=dict(batch_name=batch_name))
  jobs=batch['jobs']
  for job in jobs:
    run_job(job)
    
def assemble_job_results(*,batch_name):
  batch=kb.loadObject(key=dict(batch_name=batch_name))
  jobs=batch['jobs']
  job_results=[]
  for job in jobs:
    print('ASSEMBLING: '+job['label'])
    result=kb.loadObject(key=job)
    if not result:
      raise Exception('Unable to load object for job: '+job['label'])
    job_results.append(dict(
        job=job,
        result=result
    ))
  print('Saving results...')
  kb.saveObject(key=dict(name='job_results',batch_name=batch_name),object=dict(job_results=job_results))
  print('Done.')

def clear_job_result(job,*,incomplete_only=True):
  val=pa.get(key=job)
  if val:
    if (not incomplete_only) or (val.startswith('in-process')) or (val.startswith('error')):
      print('Clearing job: '+job['label'])
      pa.set(key=job,value=None)

def do_sort_recording(job):
  return sf_sort_recording(sorter=job['sorter'],recording=job['recording'])

def do_summarize_recording(job):
  return sf_summarize_recording(recording=job['recording'])

def do_run_job(job):
  if job['command']=='sort_recording':
    return do_sort_recording(job)
  elif job['command']=='summarize_recording':
    return do_summarize_recording(job)
  else:
    return dict(error='Invalid job command: '+job['command'])

def run_job(job):
  val=pa.get(key=job)
  if val:
    return
  code=''.join(random.choice(string.ascii_uppercase) for x in range(10))
  if not pa.set(key=job,value='in-process-'+code,overwrite=False):
    return
  print('Running job: '+job['label'])
  result=do_run_job(job)
  val=pa.get(key=job)
  if val!='in-process-'+code:
    return
  if 'error' in result:
    print('Error running job: '+result['error'])
    pa.set(key=job,value='error-'+code)
    kb.save(key=dict(job=job,name='error'),value=result)
    return
  kb.saveObject(key=job,object=result)


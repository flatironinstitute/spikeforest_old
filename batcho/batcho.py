from kbucket import client as kb
from pairio import client as pa
import random
import string

_registered_commands=dict()

def register_job_command(*, command, prepare, run):
  _registered_commands[command]=dict(
      prepare=prepare,
      run=run
  )

def prepare_batch(*, batch_name, clear_jobs=False, job_index=None):
  print('Retrieving batch {}'.format(batch_name))
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  print('Batch has {} jobs.'.format(len(jobs)))
  
  num_prepared=0
  for ii,job in enumerate(jobs):
    if (job_index is None) or (job_index==ii):
      command=job['command']
      label=job['label']
      status=_get_job_status(batch_name=batch_name, job_index=ii)
      if clear_jobs:
        if status=='finished':
          _set_job_status(batch_name=batch_name, job_index=ii, status=None)
          status=None
      if (status!='finished'):
        if command not in _registered_commands:
          raise Exception('Problem preparing job {}: command not registered: {}'.format(label,command))
        X=_registered_commands[command]
        print('Preparing job {}'.format(label))
        try:
          X['prepare'](job)
        except:
          print('Error preparing job {}'.format(label))
          raise
        num_prepared=num_prepared+1
        _set_job_status(batch_name=batch_name, job_index=ii, status='ready')
        _clear_job_lock(batch_name=batch_name, job_index=ii)
  print('Prepared {} jobs.'.format(num_prepared))

def run_batch(*, batch_name, job_index=None):
  print('Retrieving batch {}'.format(batch_name))
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  print('Batch has {} jobs.'.format(len(jobs)))
  job_code=''.join(random.choice(string.ascii_uppercase) for x in range(10))
  num_ran=0
  for ii,job in enumerate(jobs):
    if (job_index is None) or (job_index==ii):
      command=job['command']
      label=job['label']
      status=_get_job_status(batch_name=batch_name, job_index=ii)
      if status=='ready':
        if _acquire_job_lock(batch_name=batch_name, job_index=ii, code=job_code):
          print('Acquired lock for job {}'.format(label))
          if command not in _registered_commands:
            raise Exception('Problem preparing job {}: command not registered: {}'.format(label,command))
          _set_job_status(batch_name=batch_name, job_index=ii, status='running')
          X=_registered_commands[command]
          print('Running job {}'.format(label))
          try:
            result=X['run'](job)
          except:
            print('Error running job {}'.format(label))
            _set_job_status(batch_name=batch_name, job_index=ii, status='error', job_code=job_code)
            raise
          _set_job_result(batch_name=batch_name, job_index=ii, result=result, job_code=job_code)
          _set_job_status(batch_name=batch_name, job_index=ii, status='finished', job_code=job_code)
          num_ran=num_ran+1

  print('Ran {} jobs.'.format(num_ran))
  
def assemble_batch(*, batch_name):
  print('Retrieving batch {}'.format(batch_name))
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  print('Batch has {} jobs.'.format(len(jobs)))
  num_ran=0
  assembled_results=[]
  for ii,job in enumerate(jobs):
    command=job['command']
    label=job['label']
    status=_get_job_status(batch_name=batch_name, job_index=ii)
    if status=='finished':
      print('ASSEMBLING job result for {}'.format(label))
      result=_get_job_result(batch_name=batch_name, job_index=ii)
      assembled_results.append(dict(
          job=job,
          result=result
      ))
    else:
      raise Exception('Job {} not finished. Status is {}'.format(label,status))
  print('Assembling {} results'.format(len(assembled_results)))
  kb.saveObject(key=dict(name='batcho_batch_results',batch_name=batch_name),object=dict(results=assembled_results))
  
def get_batch_job_statuses(*, batch_name, job_index=None):
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  ret=[]
  for ii,job in enumerate(jobs):
    if (job_index is None) or (job_index==ii):
      status=_get_job_status(batch_name=batch_name, job_index=ii)
      ret.append(dict(
          job=job,
          status=status
      ))
  return ret
  
def set_batch(*, batch_name, jobs):
  key=dict(name='batcho_batch',batch_name=batch_name)
  kb.saveObject(key=key, object=dict(jobs=jobs))
  
def get_batch_results(*, batch_name):
  key=dict(name='batcho_batch_results',batch_name=batch_name)
  return kb.loadObject(key=key)

def _retrieve_batch(batch_name):
  key=dict(name='batcho_batch',batch_name=batch_name)
  a=pa.get(key=key)
  if not a:
    raise Exception('Unable to find batch with batch_name={}'.format(batch_name))
  try:
    obj=kb.loadObject(key=key)
  except:
    raise Exception('Unable to retrieve object for batch with batch_name={}'.format(batch_name))
  if not 'jobs' in obj:
    raise Exception('batch object does not contain jobs field for batch_name={}'.format(batch_name))
  return obj

def _get_job_status(*, batch_name, job_index):
  key=dict(name='batcho_job_status',batch_name=batch_name,job_index=job_index)
  return pa.get(key=key)

def _set_job_status(*, batch_name, job_index, status, job_code=None):
  if job_code:
    code=_get_job_lock_code(batch_name=batch_name, job_index=job_index)
    if code != job_code:
      print('Not setting job status because lock code does not match batch code')
      return
  key=dict(name='batcho_job_status',batch_name=batch_name,job_index=job_index)
  return pa.set(key=key, value=status)

def _get_job_result(*, batch_name, job_index):
  key=dict(name='batcho_job_result',batch_name=batch_name,job_index=job_index)
  return kb.loadObject(key=key)

def _set_job_result(*, batch_name, job_index, result, job_code=None):
  if job_code:
    code=_get_job_lock_code(batch_name=batch_name, job_index=job_index)
    if code != job_code:
      print('Not setting job result because lock code does not match job code')
      return
  key=dict(name='batcho_job_result',batch_name=batch_name,job_index=job_index)
  return kb.saveObject(key=key, object=result)

def _acquire_job_lock(*, batch_name, job_index, code):
  key=dict(name='batcho_job_lock',batch_name=batch_name,job_index=job_index)
  return pa.set(key=key, value=code, overwrite=False)

def _get_job_lock_code(*, batch_name, job_index):
  key=dict(name='batcho_job_lock',batch_name=batch_name,job_index=job_index)
  return pa.get(key=key)

def _clear_job_lock(*, batch_name, job_index):
  key=dict(name='batcho_job_lock',batch_name=batch_name,job_index=job_index)
  pa.set(key=key, value=None, overwrite=True)


from kbucket import client as kb
from pairio import client as pa
import random
import string
import os
import sys
import tempfile

_registered_commands=dict()

def register_job_command(*, command, prepare, run):
  _registered_commands[command]=dict(
      prepare=prepare,
      run=run
  )

def clear_batch_jobs(*, batch_name, job_index=None):
  print ('Retrieving batch {}'.format(batch_name))
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  print ('Batch has {} jobs.'.format(len(jobs)))
  
  num_cleared=0
  for ii,job in enumerate(jobs):
    if (job_index is None) or (job_index==ii):
      command=job['command']
      label=job['label']
      status=_get_job_status(batch_name=batch_name, job_index=ii)
      if status:
        _set_job_status(batch_name=batch_name, job_index=ii, status=None)
        _clear_job_lock(batch_name=batch_name, job_index=ii)
        num_cleared=num_cleared+1
  print ('Cleared {} jobs.'.format(num_cleared))


def prepare_batch(*, batch_name, clear_jobs=False, job_index=None):
  print ('Retrieving batch {}'.format(batch_name))
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  print ('Batch has {} jobs.'.format(len(jobs)))
  
  num_prepared=0
  for ii,job in enumerate(jobs):
    if (job_index is None) or (job_index==ii):
      command=job['command']
      label=job['label']
      status=_get_job_status(batch_name=batch_name, job_index=ii)
      if clear_jobs:
        if status:
          _set_job_status(batch_name=batch_name, job_index=ii, status=None)
          _clear_job_lock(batch_name=batch_name, job_index=ii)
          status=None
      if (status!='finished'):
        if command not in _registered_commands:
          raise Exception('Problem preparing job {}: command not registered: {}'.format(label,command))
        X=_registered_commands[command]
        print ('Preparing job {}'.format(label))
        try:
          X['prepare'](job)
        except:
          print ('Error preparing job {}'.format(label))
          raise
        num_prepared=num_prepared+1
        _set_job_status(batch_name=batch_name, job_index=ii, status='ready')
        _clear_job_lock(batch_name=batch_name, job_index=ii)
  print ('Prepared {} jobs.'.format(num_prepared))

def run_batch(*, batch_name, job_index=None):
  print ('Retrieving batch {}'.format(batch_name))
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  print ('Batch has {} jobs.'.format(len(jobs)))
  job_code=''.join(random.choice(string.ascii_uppercase) for x in range(10))
  num_ran=0
  for ii,job in enumerate(jobs):
    if (job_index is None) or (job_index==ii):
      command=job['command']
      label=job['label']
      status=_get_job_status(batch_name=batch_name, job_index=ii)
      if status=='ready':
        if _acquire_job_lock(batch_name=batch_name, job_index=ii, code=job_code):
          print ('Acquired lock for job {}'.format(label))
          if command not in _registered_commands:
            raise Exception('Problem preparing job {}: command not registered: {}'.format(label,command))
          _set_job_status(batch_name=batch_name, job_index=ii, status='running')
          X=_registered_commands[command]
          print ('Running job {}'.format(label))

          console_fname=_start_writing_to_file()

          try:
            result=X['run'](job)
          except:
            _stop_writing_to_file()

            print ('Error running job {}'.format(label))
            _set_job_status(batch_name=batch_name, job_index=ii, status='error', job_code=job_code)

            _set_job_console_output(batch_name=batch_name, job_index=ii, file_name=console_fname)
            os.remove(console_fname)
            raise
          _stop_writing_to_file()

          _set_job_status(batch_name=batch_name, job_index=ii, status='finished', job_code=job_code)
          _set_job_result(batch_name=batch_name, job_index=ii, result=result, job_code=job_code)

          _set_job_console_output(batch_name=batch_name, job_index=ii, file_name=console_fname)
          os.remove(console_fname)
          
          num_ran=num_ran+1

  print ('Ran {} jobs.'.format(num_ran))
  
def assemble_batch(*, batch_name):
  print ('Retrieving batch {}'.format(batch_name))
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  print ('Batch has {} jobs.'.format(len(jobs)))
  num_ran=0
  assembled_results=[]
  for ii,job in enumerate(jobs):
    command=job['command']
    label=job['label']
    status=_get_job_status(batch_name=batch_name, job_index=ii)
    if status=='finished':
      print ('ASSEMBLING job result for {}'.format(label))
      result=_get_job_result(batch_name=batch_name, job_index=ii)
      assembled_results.append(dict(
          job=job,
          result=result
      ))
    else:
      raise Exception('Job {} not finished. Status is {}'.format(label,status))
  print ('Assembling {} results'.format(len(assembled_results)))
  kb.saveObject(key=dict(name='batcho_batch_results',batch_name=batch_name),object=dict(results=assembled_results))
  
def get_batch_jobs(*, batch_name):
  batch=_retrieve_batch(batch_name)
  jobs=batch['jobs']
  return jobs

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

def get_batch_job_console_output(*, batch_name, job_index, return_url=False, verbose=False):
  key=dict(name='batcho_job_console_output',batch_name=batch_name,job_index=job_index)
  if return_url:
    url=kb.findFile(key=key,local=False,remote=True)
    return url
  else:
    fname=kb.realizeFile(key=key,verbose=verbose)
    if not fname:
      return None
    txt=_read_text_file(fname)
    return txt

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
      print ('Not setting job status because lock code does not match batch code')
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
      print ('Not setting job result because lock code does not match job code')
      return
  key=dict(name='batcho_job_result',batch_name=batch_name,job_index=job_index)
  return kb.saveObject(key=key, object=result)

def _set_job_console_output(*, batch_name, job_index, file_name, job_code=None):
  if job_code:
    code=_get_job_lock_code(batch_name=batch_name, job_index=job_index)
    if code != job_code:
      print ('Not setting job console output because lock code does not match job code')
      return
  key=dict(name='batcho_job_console_output',batch_name=batch_name,job_index=job_index)
  return kb.saveFile(key=key, fname=file_name)

def _acquire_job_lock(*, batch_name, job_index, code):
  key=dict(name='batcho_job_lock',batch_name=batch_name,job_index=job_index)
  return pa.set(key=key, value=code, overwrite=False)

def _get_job_lock_code(*, batch_name, job_index):
  key=dict(name='batcho_job_lock',batch_name=batch_name,job_index=job_index)
  return pa.get(key=key)

def _clear_job_lock(*, batch_name, job_index):
  key=dict(name='batcho_job_lock',batch_name=batch_name,job_index=job_index)
  pa.set(key=key, value=None, overwrite=True)

def _read_text_file(fname):
  with open(fname,'r') as f:
    return f.read()

_console_to_file_data=dict(
  file_handle=None,
  file_name=None,
  original_stdout=sys.stdout,
  original_stderr=sys.stderr
)

class Logger2(object):
  def __init__(self, file1, file2):
    self.file1 = file1
    self.file2 = file2
  def write(self, data):
    self.file1.write(data)
    self.file2.write(data)
  def flush(self):
    self.file1.flush()
    self.file2.flush()

def _start_writing_to_file():
  if _console_to_file_data['file_name']:
    _stop_writing_to_file()
  tmp_fname=tempfile.mktemp(suffix='.txt')
  file_handle=open(tmp_fname,'w')
  _console_to_file_data['file_name']=tmp_fname
  _console_to_file_data['file_handle']=file_handle
  sys.stdout=Logger2(file_handle,_console_to_file_data['original_stdout'])
  sys.stderr=Logger2(file_handle,_console_to_file_data['original_stderr'])
  return tmp_fname

def _stop_writing_to_file():
  sys.stdout=_console_to_file_data['original_stdout']
  sys.stderr=_console_to_file_data['original_stderr']
  fname=_console_to_file_data['file_name']
  file_handle=_console_to_file_data['file_handle']
  
  if not fname:
    return
  file_handle.close()
  _console_to_file_data['file_name']=None
  _console_to_file_data['file_handle']=None


import batcho
from kbucket import client as kb
from pairio import client as pa

def register_job_commands():
  batcho.register_job_command(
    command='summarize_recording',
    prepare=_prepare_summarize_recording,
    run=_run_summarize_recording
  )
  batcho.register_job_command(
    command='sort_recording',
    prepare=_prepare_sort_recording,
    run=_run_sort_recording
  )

def _prepare_summarize_recording(job):
  _download_recording_if_needed(job)

def _run_summarize_recording(job):
  try:
    from .summarize_recording import summarize_recording
  except:
    print('Problem importing summarize_recording. You probably need to install one or more python packages.')
    raise
  return summarize_recording(recording=job['recording'])

def _prepare_sort_recording(job):
  _download_recording_if_needed(job)

def _run_sort_recording(job):
  try:
    from .sort_recording import sort_recording
  except:
    print('Problem importing sort_recording. You probably need to install one or more python packages.')
    raise
  return sort_recording(sorter=job['sorter'],recording=job['recording'])

def _download_recording_if_needed(job):
  if 'recording' in job:
    if 'directory' in job['recording']:
      dsdir=job['recording']['directory']
      fname=dsdir+'/raw.mda'
      print('REALIZING FILE: '+fname)
      fname2=kb.realizeFile(fname)
      if not fname2:
        raise Exception('Unable to realize file: '+fname)
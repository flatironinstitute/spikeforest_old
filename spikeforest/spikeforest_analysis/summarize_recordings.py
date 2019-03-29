import time
from PIL import Image
import os
from copy import deepcopy
from mountaintools import client as mt
import mlprocessors as mlpr
import multiprocessing
# from matplotlib import pyplot as plt
from .compute_units_info import ComputeUnitsInfo
from .computerecordinginfo import ComputeRecordingInfo
import mtlogging

@mtlogging.log()
def summarize_recordings(recordings, compute_resource=None, label=None):
    print('')
    print('>>>>>> {}'.format(label or 'summarize recordings'))

    jobs_info = ComputeRecordingInfo.createJobs([
        dict(
          recording_dir=recording['directory'],
          channels=recording.get('channels',[]),
          json_out={'ext':'.json','upload':True},
          _container='default',
          _label='Summarize recording: '+recording.get('name', '')
        )
        for recording in recordings
    ])

    jobs_units_info = ComputeUnitsInfo.createJobs([
        dict(
          recording_dir=recording['directory'],
          firings=recording['directory']+'/firings_true.mda',
          unit_ids=recording.get('units_true',None),
          channel_ids=recording.get('channels',None),
          json_out={'ext':'.json','upload':True},
          _container='default',
          _label='Compute units info for recording: '+recording.get('name', '')
        )
        for recording in recordings
    ])
    
    # all_jobs=jobs_info+jobs_timeseries_plot+jobs_units_info
    all_jobs=jobs_info+jobs_units_info
    label=label or 'Summarize recordings'
    mlpr.executeBatch(jobs=all_jobs,label=label,num_workers=None,compute_resource=compute_resource)

    print('Gathering summarized recordings...')

    summarized_recordings = deepcopy(recordings)
    for ii in range(len(recordings)):
      summary = dict()

      result0 = jobs_info[ii].result
      summary['computed_info'] = mt.loadObject(path=result0.outputs['json_out'])
      summary['plots']=dict()
    
      result0=jobs_units_info[ii].result
      summary['true_units_info']=mt.getSha1Url(path=result0.outputs['json_out'], basename='true_units_info.json')
      
      summarized_recordings[ii]['summary'] = summary

    return summarized_recordings

def _create_jobs_for_recording_old(recording):
    print('Creating jobs for recording: {}/{}'.format(recording.get('study',''),recording.get('name','')))
    dsdir=recording['directory']
    # raw_path=dsdir+'/raw.mda'
    firings_true_path=dsdir+'/firings_true.mda'
    # geom_path=dsdir+'/geom.csv'
    channels=recording.get('channels',None)
    units=recording.get('units_true',None)

    if not mt.findFile(path=firings_true_path):
        raise Exception('firings_true file not found: '+firings_true_path)
    job_info=ComputeRecordingInfo.createJob(
        recording_dir=dsdir,
        channels=recording.get('channels',[]),
        json_out={'ext':'.json','upload':True},
        _container='default'
    )
    job_info.addFilesToRealize([dsdir+'/raw.mda',dsdir+'/firings_true.mda'])
    # job=CreateTimeseriesPlot.createJob(
    #     recording_dir=dsdir,
    #     channels=recording.get('channels',[]),
    #     jpg_out={'ext':'.jpg','upload':True},
    #     _container='default'
    # )
    # jobs_timeseries_plot.append(job)
    job_units_info=ComputeUnitsInfo.createJob(
        recording_dir=dsdir,
        firings=dsdir+'/firings_true.mda',
        unit_ids=units,
        channel_ids=channels,
        json_out={'ext':'.json','upload':True},
        _container='default'
    )
    job_units_info.addFilesToRealize([dsdir+'/raw.mda', dsdir+'/firings_true.mda'])
    return (job_info, job_units_info)
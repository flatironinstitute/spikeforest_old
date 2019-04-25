from mountaintools import client as mt
import spikeextractors as si
import mlprocessors as mlpr
import os
import shutil
import random
import string
import multiprocessing
import mtlogging
#from . import sorters as sorters

from spikesorters import MountainSort4, SpykingCircus, YASS, IronClust, KiloSort, KiloSort2, MountainSort4TestError
        
Processors=dict(
    MountainSort4=(MountainSort4, 'default'),
    IronClust=(IronClust,None),
    SpykingCircus=(SpykingCircus,'default'),
    KiloSort=(KiloSort,None),
    KiloSort2=(KiloSort2,None),
    Yass=(YASS,'default'),
    MountainSort4TestError=(MountainSort4TestError, 'default')
)

@mtlogging.log()
def sort_recordings(*,sorter,recordings,num_workers=None,disable_container=False, compute_resource, job_timeout=60*20, label=None):
    print('')
    print('>>>>>> {}'.format(label or 'sort recordings'))
    sorting_params=sorter['params']
    processor_name=sorter['processor_name']
    if processor_name in Processors:
        SS=Processors[processor_name][0]
        SS_container=Processors[processor_name][1]
        if disable_container:
            SS_container=None
    else:
        raise Exception('No such sorter: '+processor_name)

    if SS_container:
        if SS_container=='default':
            SS_container=SS.CONTAINER
        print('Locating container: '+SS_container)
        if not mt.findFile(path=SS_container):
            raise Exception('Unable to realize container: '+SS_container)
        
    print('>>>>>>>>>>> Sorting recordings using {}'.format(processor_name))

    # pool = multiprocessing.Pool(20)
    # sorting_jobs=pool.map(_create_sorting_job_for_recording_helper, [dict(recording=recording, sorter=sorter, job_timeout=job_timeout) for recording in recordings])
    # pool.close()
    # pool.join()



    sorting_params=sorter['params']
    processor_name=sorter['processor_name']

    sorting_jobs=SS.createJobs([
        dict(
            _container=SS_container,
            _timeout=job_timeout,
            _label='Sort recording {}/{} using {}'.format(recording.get('study', ''), recording.get('name', ''), sorter.get('name', '')),
            _additional_files_to_realize=[recording['directory']+'/raw.mda'],
            _compute_resource=sorter.get('compute_resource', None),
            recording_dir=recording['directory'],
            channels=recording.get('channels',[]),
            firings_out=dict(ext='.mda',upload=True),
            **sorting_params
        )
        for recording in recordings
    ])

    label=label or 'Sort recordings using {}'.format(processor_name)
    sorting_job_results = mlpr.executeBatch(jobs=sorting_jobs,label=label,num_workers=num_workers,compute_resource=compute_resource)
    
    print('Gathering sorting results...')
    sorting_results = [
        dict(
            recording=recording,
            sorter=sorter,
            firings_true=recording['directory']+'/firings_true.mda',
            processor_name=SS.NAME,
            processor_version=SS.VERSION,
            execution_stats=sorting_job_results[ii].runtime_info,
            console_out=sorting_job_results[ii].console_out,
            container=SS_container,
            firings=(sorting_job_results[ii].outputs or dict()).get('firings_out', None)
        )
        for ii, recording in enumerate(recordings)
    ]

    return sorting_results
    

@mtlogging.log()
def multi_sort_recordings(*,sorters,recordings,num_workers=None,disable_container=False, job_timeout=60*20, label=None):
    print('')
    print('>>>>>> {}'.format(label or 'sort recordings'))

    sorting_jobs_by_compute_resource = dict()
    sorting_results_by_compute_resource = dict()

    # initialize
    for sorter in sorters:
        compute_resource = sorter.get('compute_resource', None)
        if compute_resource not in sorting_jobs_by_compute_resource:
            sorting_jobs_by_compute_resource[compute_resource] = []
            sorting_results_by_compute_resource[compute_resource] = []

    sorting_results = []
    for sorter in sorters:
        sorting_params=sorter['params']
        processor_name=sorter['processor_name']
        if processor_name in Processors:
            SS=Processors[processor_name][0]
            SS_container=Processors[processor_name][1]
            if disable_container:
                SS_container=None
        else:
            raise Exception('No such sorter: '+processor_name)

        if SS_container:
            if SS_container=='default':
                SS_container=SS.CONTAINER
            print('Locating container: '+SS_container)
            if not mt.findFile(path=SS_container):
                raise Exception('Unable to realize container: '+SS_container)

        sorting_params=sorter['params']
        processor_name=sorter['processor_name']
        compute_resource=sorter.get('compute_resource', None)

        sorting_jobs0 = SS.createJobs([
            dict(
                _container=SS_container,
                _timeout=job_timeout,
                _label='Sort recording {}/{} using {}'.format(recording.get('study', ''), recording.get('name', ''), sorter.get('name', '')),
                _additional_files_to_realize=[recording['directory']+'/raw.mda'],
                _compute_resource=sorter.get('compute_resource', None),
                recording_dir=recording['directory'],
                channels=recording.get('channels',[]),
                firings_out=dict(ext='.mda',upload=True),
                **sorting_params
            )
            for recording in recordings
        ])

        sorting_jobs_by_compute_resource[compute_resource].extend(sorting_jobs0)

        sorting_results_by_compute_resource[compute_resource].extend([
            dict(
                recording=recording,
                sorter=sorter,
                firings_true=recording['directory']+'/firings_true.mda',
                processor_name=SS.NAME,
                processor_version=SS.VERSION,
                container=SS_container,
                # firings, execution_stats, and console_out will be filled in once the job completes
            )
            for ii, recording in enumerate(recordings)
        ])

    
    sorting_results = []
    for compute_resource, sorting_jobs0 in sorting_jobs_by_compute_resource.items():
        label=label or 'Sort recordings (resource={})'.format(compute_resource)
        sorting_job_results0 = mlpr.executeBatch(jobs=sorting_jobs0,label=label,num_workers=num_workers,compute_resource=compute_resource)
        sorting_results0 = sorting_results_by_compute_resource[compute_resource]
        for ii, sr in enumerate(sorting_results0):
            sr['execution_stats'] = sorting_job_results0[ii].runtime_info
            sr['console_out'] = sorting_job_results0[ii].console_out
            sr['firings'] = (sorting_job_results0[ii].outputs or dict()).get('firings_out', None)
        sorting_results.extend(sorting_results0)

    return sorting_results
    

    
    

from mountaintools import client as mt
from spikeforest import spikeextractors as si
import mlprocessors as mlpr
import os
import shutil
import random
import string
import multiprocessing
#from . import sorters as sorters

from spikesorters import MountainSort4, SpykingCircus, YASS, IronClust, KiloSort, KiloSort2, MountainSort4TestError

"""
class IronClust(mlpr.Processor):
    NAME='IronClust'
    VERSION='4.3.0'
    
    recording_dir=mlpr.Input('Directory of recording',directory=True)
    channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
    firings_out=mlpr.Output('Output firings file')
    
    detect_sign=mlpr.IntegerParameter('Use -1, 0, or 1, depending on the sign of the spikes in the recording')
    adjacency_radius=mlpr.FloatParameter('Use -1 to include all channels in every neighborhood')
    detect_threshold=mlpr.FloatParameter(optional=True,default=3,description='')
    prm_template_name=mlpr.StringParameter(optional=False,description='TODO')
    freq_min=mlpr.FloatParameter(optional=True,default=300,description='Use 0 for no bandpass filtering')
    freq_max=mlpr.FloatParameter(optional=True,default=6000,description='Use 0 for no bandpass filtering')
    merge_thresh=mlpr.FloatParameter(optional=True,default=0.98,description='TODO')
    pc_per_chan=mlpr.IntegerParameter(optional=True,default=3,description='TODO')
    
    def run(self):
        ironclust_src=os.environ.get('IRONCLUST_SRC',None)
        if not ironclust_src:
            raise Exception('Environment variable not set: IRONCLUST_SRC')
        code=''.join(random.choice(string.ascii_uppercase) for x in range(10))
        tmpdir=os.environ.get('TEMPDIR','/tmp')+'/ironclust-tmp-'+code
            
        try:
            recording=si.MdaRecordingExtractor(self.recording_dir)
            if len(self.channels)>0:
              recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
            sorting=sorters.ironclust(
                recording=recording,
                tmpdir=tmpdir, ## TODO
                detect_sign=self.detect_sign,
                adjacency_radius=self.adjacency_radius,
                detect_threshold=self.detect_threshold,
                merge_thresh=self.merge_thresh,
                freq_min=self.freq_min,
                freq_max=self.freq_max,
                pc_per_chan=self.pc_per_chan,
                prm_template_name=self.prm_template_name,
                ironclust_src=ironclust_src
            )
            si.MdaSortingExtractor.writeSorting(sorting=sorting,save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            raise
        shutil.rmtree(tmpdir)
"""

# class SpykingCircus(mlpr.Processor):
#     NAME='SpykingCircus'
#     VERSION='0.1.7'
    
#     recording_dir=mlpr.Input('Directory of recording',directory=True)
#     #singularity_container=mlpr.Input('Singularity container',optional=False)
#     channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
#     firings_out=mlpr.Output('Output firings file')
    
#     detect_sign=mlpr.IntegerParameter(description='-1, 1, or 0')
#     adjacency_radius=mlpr.FloatParameter(optional=True,default=100,description='Channel neighborhood adjacency radius corresponding to geom file')
#     spike_thresh=mlpr.FloatParameter(optional=True,default=6,description='Threshold for detection')
#     template_width_ms=mlpr.FloatParameter(optional=True,default=3,description='Spyking circus parameter')
#     filter=mlpr.BoolParameter(optional=True,default=True)
#     whitening_max_elts=mlpr.IntegerParameter(optional=True,default=1000,description='I believe it relates to subsampling and affects compute time')
#     clustering_max_elts=mlpr.IntegerParameter(optional=True,default=10000,description='I believe it relates to subsampling and affects compute time')

#     def run(self):
#         singularity_container=os.environ.get('SC_SINGULARITY_CONTAINER',None)
#         if not singularity_container:
#             raise Exception('You must set the environment variable SC_SINGULARITY_CONTAINER.')

#         code=''.join(random.choice(string.ascii_uppercase) for x in range(10))
#         tmpdir=os.environ.get('TEMPDIR','/tmp')+'/ironclust-tmp-'+code
        
#         num_workers=os.environ.get('NUM_WORKERS',1)
            
#         try:
#             recording=si.MdaRecordingExtractor(self.recording_dir)
#             if len(self.channels)>0:
#               recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
#             if not os.path.exists(tmpdir):
#                 os.mkdir(tmpdir)
#             sorting=sorters.spyking_circus(
#                 recording=recording,
#                 output_folder=tmpdir,
#                 probe_file=None,
#                 file_name=None,
#                 detect_sign=self.detect_sign,
#                 adjacency_radius=self.adjacency_radius,
#                 spike_thresh=self.spike_thresh,
#                 template_width_ms=self.template_width_ms,
#                 filter=self.filter,
#                 merge_spikes=True,
#                 n_cores=num_workers,
#                 electrode_dimensions=None,
#                 whitening_max_elts=self.whitening_max_elts,
#                 clustering_max_elts=self.clustering_max_elts,
#                 singularity_container=singularity_container
#             )
#             si.MdaSortingExtractor.writeSorting(sorting=sorting,save_path=self.firings_out)
#         except:
#             if os.path.exists(tmpdir):
#                 shutil.rmtree(tmpdir)
#             raise
#         shutil.rmtree(tmpdir)


"""
class KiloSort(mlpr.Processor):
    NAME='KiloSort'
    VERSION='0.1.1' # wrapper VERSION
    ADDITIONAL_FILES=['*.m']
    
    recording_dir=mlpr.Input('Directory of recording',directory=True)
    channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
    firings_out=mlpr.Output('Output firings file')
    
    detect_sign=mlpr.IntegerParameter('Use -1 or 1, depending on the sign of the spikes in the recording')
    adjacency_radius=mlpr.FloatParameter('Use -1 to include all channels in every neighborhood')
    detect_threshold=mlpr.FloatParameter(optional=True,default=3,description='')
    #prm_template_name=mlpr.StringParameter(optional=False,description='TODO')
    freq_min=mlpr.FloatParameter(optional=True,default=300,description='Use 0 for no bandpass filtering')
    freq_max=mlpr.FloatParameter(optional=True,default=6000,description='Use 0 for no bandpass filtering')
    merge_thresh=mlpr.FloatParameter(optional=True,default=0.98,description='TODO')
    pc_per_chan=mlpr.IntegerParameter(optional=True,default=3,description='TODO')
    
    def run(self):
        code=''.join(random.choice(string.ascii_uppercase) for x in range(10))
        tmpdir=os.environ.get('TEMPDIR','/tmp')+'/kilosort-tmp-'+code
            
        try:
            recording=si.MdaRecordingExtractor(self.recording_dir)
            if len(self.channels)>0:
              recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
            sorting=sorters.kilosort(
                recording=recording,
                tmpdir=tmpdir, 
                detect_sign=self.detect_sign,
                adjacency_radius=self.adjacency_radius,
                detect_threshold=self.detect_threshold,
                merge_thresh=self.merge_thresh,
                freq_min=self.freq_min,
                freq_max=self.freq_max,
                pc_per_chan=self.pc_per_chan
            )
            si.MdaSortingExtractor.writeSorting(sorting=sorting,save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            raise
        shutil.rmtree(tmpdir)
"""
#sf.sorters.ironclust(*, recording, tmpdir, detect_sign=-1, adjacency_radius=-1, detect_threshold=5, merge_thresh=0.98, freq_min=300, freq_max=6000, pc_per_chan=3, prm_template_name, ironclust_src=None)
        
Processors=dict(
    MountainSort4=(MountainSort4, 'default'),
    IronClust=(IronClust,None),
    SpykingCircus=(SpykingCircus,'default'),
    KiloSort=(KiloSort,None),
    KiloSort2=(KiloSort2,None),
    Yass=(YASS,'default'),
    MountainSort4TestError=(MountainSort4TestError, 'default')
)

def _create_sorting_job_for_recording_helper(kwargs):
    return _create_sorting_job_for_recording(**kwargs)

def _create_sorting_job_for_recording(recording, sorter):
    print('Creating sorting job for recording: {}/{} ({})'.format(recording.get('study',''),recording.get('name',''),sorter['processor_name']))

    sorting_params=sorter['params']
    processor_name=sorter['processor_name']
    SS=Processors[processor_name][0]
    SS_container=Processors[processor_name][1]

    dsdir=recording['directory']
    job=SS.createJob(
        _container=SS_container,
        recording_dir=dsdir,
        channels=recording.get('channels',[]),
        firings_out=dict(ext='.mda',upload=True),
        **sorting_params
    )
    job.addFilesToRealize(dsdir+'/raw.mda')
    return job

def _gather_sorting_result_for_recording_helper(kwargs):
    return _gather_sorting_result_for_recording(**kwargs)

def _gather_sorting_result_for_recording(recording, sorter, sorting_job):
    firings_true_path=recording['directory']+'/firings_true.mda'

    result0=sorting_job.result
    outputs0=result0.outputs
    console_out=(mt.loadText(path=result0.console_out) or '')

    processor_name=sorter['processor_name']
    SS=Processors[processor_name][0]
    SS_container=Processors[processor_name][1]

    result=dict(
        recording=recording,
        sorter=sorter,
        firings_true=firings_true_path,
        processor_name=SS.NAME,
        processor_version=SS.VERSION,
        execution_stats=result0.runtime_info,
        console_out=mt.saveText(text=console_out,basename='console_out.txt'),
        container=SS_container,
        firings=outputs0.get('firings_out', None)
    )
    return result
        
def sort_recordings(*,sorter,recordings,compute_resource=None,num_workers=None,disable_container=False):
    print('>>>>>> sort recordings')
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

    pool = multiprocessing.Pool(20)
    sorting_jobs=pool.map(_create_sorting_job_for_recording_helper, [dict(recording=recording, sorter=sorter) for recording in recordings])
    pool.close()
    pool.join()

    # sorting_jobs=[]
    # for recording in recordings:
    #     print('Creating sorting job for recording: {}/{} ({})'.format(recording.get('study',''),recording.get('name',''),sorter['processor_name']))
    #     dsdir=recording['directory']
    #     job=SS.createJob(
    #         _container=SS_container,
    #         recording_dir=dsdir,
    #         channels=recording.get('channels',[]),
    #         firings_out=dict(ext='.mda',upload=True),
    #         **sorting_params
    #     )
    #     sorting_jobs.append(job)

    label='Sort recordings using {}'.format(processor_name)
    mlpr.executeBatch(jobs=sorting_jobs,label=label,compute_resource=compute_resource,num_workers=num_workers)
    
    print('Gathering sorting results...')

    pool = multiprocessing.Pool(20)
    sorting_results=pool.map(_gather_sorting_result_for_recording_helper, [dict(recording=recordings[ii], sorting_job=sorting_jobs[ii], sorter=sorter) for ii in range(len(recordings))])
    pool.close()
    pool.join()

    return sorting_results
    

    

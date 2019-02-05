from kbucket import client as kb
import spikeextractors as si
import mlprocessors as mlpr
import os
import shutil
import random
import string
from . import sorters as sorters

from spikesorters import MountainSort4, SpykingCircus
    

class IronClust(mlpr.Processor):
    NAME='IronClust'
    VERSION='4.2.8'
    
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

class KiloSort(mlpr.Processor):
    NAME='KiloSort'
    VERSION='0.1.0' # wrapper version
    
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

#sf.sorters.ironclust(*, recording, tmpdir, detect_sign=-1, adjacency_radius=-1, detect_threshold=5, merge_thresh=0.98, freq_min=300, freq_max=6000, pc_per_chan=3, prm_template_name, ironclust_src=None)
        
Processors=dict(
    MountainSort4=(MountainSort4,'sha1://a3842053423c633b62e70474be9d76068cdc1ea5/mountainsort4.simg'),
    IronClust=(IronClust,None),
    SpykingCircus=(SpykingCircus,'sha1://487fe664853285e65f8130a1138a4415f8acc4ca/spyking_circus.simg'),
    KiloSort=(KiloSort,None)
)
        
def sort_recording(*,sorter,recording):
    dsdir=recording['directory']
    sorting_params=sorter['params']
    processor_name=sorter['processor_name']
    if processor_name in Processors:
        SS=Processors[processor_name][0]
        SS_container=Processors[processor_name][1]
    else:
        raise Exception('No such sorter: '+processor_name)

    if SS_container:
        print('Locating container: '+SS_container)
        if not kb.realizeFile(SS_container):
            raise Exception('Unable to realize container: '+SS_container)
        
    print('Sorting recording {} using {}'.format(dsdir, processor_name))
    X=SS.execute(
        _container=SS_container,
        recording_dir=dsdir,
        channels=recording.get('channels',[]),
        firings_out=dict(ext='.mda'),
        **sorting_params
    )
    outputs=X.outputs
    stats=X.stats
    console_out=X.console_out
    print('Saving firings_out...')
    firings_out=kb.saveFile(outputs['firings_out'])
    firings_true_path=recording['directory']+'/firings_true.mda'
    if not kb.findFile(firings_true_path):
        firings_true_path=None
    print('Assembling result...')
    result=dict(
        recording_name=recording.get('name',None),
        study_name=recording.get('study',None),
        sorter_name=sorter.get('name',None),
        recording_dir=dsdir,
        channels=recording.get('channels',[]),
        units_true=recording.get('units_true',[]),
        firings_true=firings_true_path,
        sorting_params=sorting_params,
        processor_name=SS.NAME,
        processor_version=SS.VERSION,
        execution_stats=stats,
        console_out=kb.saveText(text=console_out,basename='console_out.txt'),
        container=SS_container,
        firings=firings_out
    )
    print('Done sorting.')
    return result

from kbucket import client as kb
import spikeextractors as si
import mlprocessors as mlpr
import os
import shutil
import random
import string
from . import sorters as sorters
from .summarize_sorting import summarize_sorting
from .compare_with_truth import compare_with_truth

class MountainSort4(mlpr.Processor):
    NAME='MountainSort4'
    VERSION='4.0.1'
    
    recording_dir=mlpr.Input('Directory of recording',directory=True)
    channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
    firings_out=mlpr.Output('Output firings file')
    
    detect_sign=mlpr.IntegerParameter('Use -1, 0, or 1, depending on the sign of the spikes in the recording')
    adjacency_radius=mlpr.FloatParameter('Use -1 to include all channels in every neighborhood')
    freq_min=mlpr.FloatParameter(optional=True,default=300,description='Use 0 for no bandpass filtering')
    freq_max=mlpr.FloatParameter(optional=True,default=6000,description='Use 0 for no bandpass filtering')
    whiten=mlpr.BoolParameter(optional=True,default=True,description='Whether to do channel whitening as part of preprocessing')
    clip_size=mlpr.IntegerParameter(optional=True,default=50,description='')
    detect_threshold=mlpr.FloatParameter(optional=True,default=3,description='')
    detect_interval=mlpr.IntegerParameter(optional=True,default=10,description='Minimum number of timepoints between events detected on the same channel')
    noise_overlap_threshold=mlpr.FloatParameter(optional=True,default=0.15,description='Use None for no automated curation')
    
    def run(self):
        recording=si.MdaRecordingExtractor(self.recording_dir)
        if len(self.channels)>0:
          recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
        num_workers=os.environ.get('NUM_WORKERS',None)
        if num_workers:
            num_workers=int(num_workers)
        sorting=sorters.mountainsort4(
            recording=recording,
            detect_sign=self.detect_sign,
            adjacency_radius=self.adjacency_radius,
            freq_min=self.freq_min,
            freq_max=self.freq_max,
            whiten=self.whiten,
            clip_size=self.clip_size,
            detect_threshold=self.detect_threshold,
            detect_interval=self.detect_interval,
            noise_overlap_threshold=self.noise_overlap_threshold,
            num_workers=num_workers
        )
        si.MdaSortingExtractor.writeSorting(sorting=sorting,save_path=self.firings_out)
    

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
        
class SpykingCircus(mlpr.Processor):
    NAME='SpykingCircus'
    VERSION='0.1.5'
    
    recording_dir=mlpr.Input('Directory of recording',directory=True)
    channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
    firings_out=mlpr.Output('Output firings file')
    
    detect_sign=mlpr.IntegerParameter(description='-1, 1, or 0')
    adjacency_radius=mlpr.FloatParameter(optional=True,default=100,description='Channel neighborhood adjacency radius corresponding to geom file')
    spike_thresh=mlpr.FloatParameter(optional=True,default=6,description='Threshold for detection')
    template_width_ms=mlpr.FloatParameter(optional=True,default=3,description='Spyking circus parameter')
    filter=mlpr.BoolParameter(optional=True,default=True)
    whitening_max_elts=mlpr.IntegerParameter(optional=True,default=1000,description='I believe it relates to subsampling and affects compute time')
    clustering_max_elts=mlpr.IntegerParameter(optional=True,default=10000,description='I believe it relates to subsampling and affects compute time')
    
    def run(self):
        code=''.join(random.choice(string.ascii_uppercase) for x in range(10))
        tmpdir=os.environ.get('TEMPDIR','/tmp')+'/ironclust-tmp-'+code
        
        num_workers=os.environ.get('NUM_WORKERS',1)
            
        try:
            recording=si.MdaRecordingExtractor(self.recording_dir)
            if len(self.channels)>0:
              recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
            sorting=sorters.spyking_circus(
                recording=recording,
                output_folder=tmpdir,
                probe_file=None,
                file_name=None,
                detect_sign=self.detect_sign,
                adjacency_radius=self.adjacency_radius,
                spike_thresh=self.spike_thresh,
                template_width_ms=self.template_width_ms,
                filter=self.filter,
                merge_spikes=True,
                n_cores=num_workers,
                electrode_dimensions=None,
                whitening_max_elts=self.whitening_max_elts,
                clustering_max_elts=self.clustering_max_elts,
                singularity_container=os.environ.get('SC_SINGULARITY_CONTAINER',None)
            )
            si.MdaSortingExtractor.writeSorting(sorting=sorting,save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            raise
        shutil.rmtree(tmpdir)


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
    MountainSort4=MountainSort4,
    IronClust=IronClust,
    SpykingCircus=SpykingCircus,
    KiloSort=KiloSort
)
        
def sort_recording(sorter,recording):
    dsdir=recording['directory']
    sorting_params=sorter['params']
    processor_name=sorter['processor_name']
    if processor_name in Processors:
        SS=Processors[processor_name]
    else:
        raise Exception('No such sorter: '+processor_name)
        
    outputs=SS.execute(
        recording_dir=dsdir,
        channels=recording.get('channels',[]),
        firings_out=dict(ext='.mda'),
        **sorting_params
    ).outputs
    firings_out=kb.saveFile(outputs['firings_out'])
    firings_true_path=recording['directory']+'/firings_true.mda'
    if not kb.findFile(firings_true_path):
        firings_true_path=None
    result=dict(
        recording_name=recording['name'],
        study_name=recording['study'],
        sorter_name=sorter['name'],
        recording_dir=dsdir,
        channels=recording.get('channels',[]),
        units_true=recording.get('units_true',[]),
        firings_true=firings_true_path,
        sorting_params=sorting_params,
        sorting_processor_name=SS.NAME,
        sorting_processor_version=SS.VERSION,
        firings=firings_out
    )
    result['summary']=summarize_sorting(result)
    if result.get('firings_true',None):
        result['comparison_with_truth']=compare_with_truth(result)
    
    return result

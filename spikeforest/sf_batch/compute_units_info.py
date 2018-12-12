import numpy as np
import json
import mlprocessors as mlpr
import spikeextractors as si
import spikewidgets as sw
from kbucket import client as kb

def write_json_file(fname,obj):
  with open(fname, 'w') as f:
    json.dump(obj, f)

def get_random_spike_waveforms(*,recording,sorting,unit,snippet_len,max_num,channels=None):
    st=sorting.getUnitSpikeTrain(unit_id=unit)
    num_events=len(st)
    if num_events>max_num:
        event_indices=np.random.choice(range(num_events),size=max_num,replace=False)
    else:
        event_indices=range(num_events)

    spikes=recording.getSnippets(reference_frames=st[event_indices].astype(int),snippet_len=snippet_len,channel_ids=channels)
    if spikes:
      spikes=np.dstack(tuple(spikes))
    else:
      spikes=np.zeros((recording.getNumChannels(),snippet_len,0))
    return spikes

def compute_unit_templates(*,recording,sorting,unit_ids,snippet_len=50):
    ret=[]
    for unit in unit_ids:
        #print('Unit {} of {}'.format(unit,len(unit_ids)))
        waveforms=get_random_spike_waveforms(recording=recording,sorting=sorting,unit=unit,snippet_len=snippet_len,max_num=100)
        template=np.mean(waveforms,axis=2)
        ret.append(template)
    return ret

def compute_template_snr(template,channel_noise_levels):
    channel_snrs=[]
    for ch in range(template.shape[0]):
        channel_snrs.append((np.max(template[ch,:])-np.min(template[ch,:]))/channel_noise_levels[ch])
    return float(np.max(channel_snrs))
    
def compute_channel_noise_levels(recording):
    channel_ids=recording.getChannelIds()
    M=len(channel_ids)
    X=recording.getTraces(start_frame=0,end_frame=int(np.minimum(1000,recording.getNumFrames())))
    ret=[]
    for ii in range(len(channel_ids)):
        noise_level=np.std(X[ii,:])
        ret.append(noise_level)
    return ret

class MemoryRecordingExtractor(si.RecordingExtractor):
    def __init__(self, parent_recording):
        si.RecordingExtractor.__init__(self)
        self._parent_recording=parent_recording
        self._traces=parent_recording.getTraces()
        self.copyChannelProperties(parent_recording)
        self._channel_index_map=dict()
        ids=parent_recording.getChannelIds()
        for ii,id in enumerate(ids):
          self._channel_index_map[id]=ii
        self._copy_channel_properties(parent_recording)

    def getTraces(self, channel_ids=None, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame=0
        if end_frame is None:
            end_frame=self.getNumFrames()
        if channel_ids is None:
            channel_ids=self.getChannelIds()
        channel_indices=[]
        for id in channel_ids:
          channel_indices.append(self._channel_index_map[id])
        return self._traces[channel_indices,start_frame:end_frame]

    def getChannelIds(self):
        return self._parent_recording.getChannelIds()

    def getNumFrames(self):
        return self._parent_recording.getNumFrames()

    def getSamplingFrequency(self):
        return self._parent_recording.getSamplingFrequency()

    def frameToTime(self, frame):
        return self._parent_recording.frameToTime(frame)

    def timeToFrame(self, time):
        return self._parent_recording.timeToFrame(time)

    def _copy_channel_properties(self, recording, channel_ids=None):
        if channel_ids is None:
            channel_ids=recording.getChannelIds()
        for id in channel_ids:
          pnames=recording.getChannelPropertyNames(channel_id=id)
          for pname in pnames:
            val=recording.getChannelProperty(channel_id=id,property_name=pname)
            self.setChannelProperty(channel_id=id,property_name=pname,value=val)

class ComputeUnitsInfo(mlpr.Processor):
  NAME='ComputeUnitsInfo'
  VERSION='0.1.1'
  recording_dir=mlpr.Input(directory=True,description='Recording directory')
  channel_ids=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
  unit_ids=mlpr.IntegerListParameter(description='List of units to use.',optional=True,default=[])
  firings=mlpr.Input(description='Firings file')
  json_out=mlpr.Output('The info as a .json file')
  
  def run(self):
    R0=si.MdaRecordingExtractor(dataset_directory=self.recording_dir,download=True)
    if (self.channel_ids) and (len(self.channel_ids)>0):
      R0=si.SubRecordingExtractor(parent_recording=R0,channel_ids=self.channel_ids)
    recording=sw.lazyfilters.bandpass_filter(recording=R0,freq_min=300,freq_max=6000)
    sorting=si.MdaSortingExtractor(firings_file=self.firings)
    ef=int(1e6)
    recording_sub=si.SubRecordingExtractor(parent_recording=recording,start_frame=0,end_frame=ef)
    recording_sub=MemoryRecordingExtractor(parent_recording=recording_sub)
    sorting_sub=si.SubSortingExtractor(parent_sorting=sorting,start_frame=0,end_frame=ef)
    unit_ids=self.unit_ids
    if (not unit_ids) or (len(unit_ids)==0):
      unit_ids=sorting.getUnitIds()
  
    channel_noise_levels=compute_channel_noise_levels(recording=recording)
    print('computing templates...')
    templates=compute_unit_templates(recording=recording_sub,sorting=sorting_sub,unit_ids=unit_ids)
    print('.')
    ret=[]
    for i,unit_id in enumerate(unit_ids):
      template=templates[i]
      info0=dict()
      info0['unit_id']=int(unit_id)
      info0['snr']=compute_template_snr(template,channel_noise_levels)
      peak_channel_index=np.argmax(np.max(np.abs(template),axis=1))
      info0['peak_channel']=int(recording.getChannelIds()[peak_channel_index])
      train=sorting.getUnitSpikeTrain(unit_id=unit_id)
      info0['num_events']=int(len(train))
      info0['firing_rate']=float(len(train)/(recording.getNumFrames()/recording.getSamplingFrequency()))
      ret.append(info0)
    write_json_file(self.json_out,ret)
  
  
## return format can be 'json' or 'filename'
def compute_units_info(*,recording_dir,firings,channel_ids=[],unit_ids=[],return_format='json'):
    out=ComputeUnitsInfo.execute(recording_dir=recording_dir,firings=firings,unit_ids=unit_ids,channel_ids=channel_ids,json_out={'ext':'.json'}).outputs
    fname=out['json_out']
    if return_format=='filename':
      return fname
    else:
      fname=kb.realizeFile(fname)
      with open(fname) as f:
        return json.load(f)

def select_units_on_channels(recording_dir,firings,channels):
  info=compute_units_info(recording_dir=recording_dir,firings=firings)
  units=[]
  for info0 in info:
    if info0['peak_channel'] in channels:
      units.append(info0['unit_id'])
  return units
import numpy as np
import json
import mlprocessors as mlpr
from cairio import client as ca

try:
  # if we are running this outside the container
  import spikeforest.spikeextractors as si
  import spikeforest.spikewidgets as sw
except:
  # if we are in the container
  import spikeextractors as si
  import spikewidgets as sw

_CONTAINER='sha1://3b26155930cc4a4745c67b702ce297c9c968ac94/02-12-2019/mountaintools_basic.simg'

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
    if len(spikes)>0:
      spikes=np.dstack(tuple(spikes))
    else:
      spikes=np.zeros((recording.getNumChannels(),snippet_len,0))
    return spikes

def compute_unit_templates(*,recording,sorting,unit_ids,snippet_len=50,max_num=100,channels=None):
    ret=[]
    for unit in unit_ids:
        # print('Unit {} of {}'.format(unit,len(unit_ids)))
        waveforms=get_random_spike_waveforms(recording=recording,sorting=sorting,unit=unit,snippet_len=snippet_len,max_num=max_num,channels=None)
        template=np.median(waveforms,axis=2)
        ret.append(template)
    return ret

def compute_template_snr(template,channel_noise_levels):
    channel_snrs=[]
    for ch in range(template.shape[0]):
        #channel_snrs.append((np.max(template[ch,:])-np.min(template[ch,:]))/channel_noise_levels[ch])
        channel_snrs.append((np.max(np.abs(template[ch,:])))/channel_noise_levels[ch])
    return float(np.max(channel_snrs))
    
def compute_channel_noise_levels(recording):
    channel_ids=recording.getChannelIds()
    M=len(channel_ids)
    samplerate=int(recording.getSamplingFrequency())
    X=recording.getTraces(start_frame=samplerate*1,end_frame=samplerate*2)
    ret=[]
    for ii in range(len(channel_ids)):
        #noise_level=np.std(X[ii,:])
        noise_level=np.median(np.abs(X[ii,:]))/0.6745 # median absolute deviation (MAD)
        ret.append(noise_level)
    return ret

class ComputeUnitsInfo(mlpr.Processor):
  NAME='ComputeUnitsInfo'
  VERSION='0.1.5k'
  CONTAINER=_CONTAINER
  recording_dir=mlpr.Input(directory=True,description='Recording directory')
  channel_ids=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
  unit_ids=mlpr.IntegerListParameter(description='List of units to use.',optional=True,default=[])
  firings=mlpr.Input(description='Firings file')
  json_out=mlpr.Output('The info as a .json file')
  
  def run(self):
    R0=si.MdaRecordingExtractor(dataset_directory=self.recording_dir,download=True)
    if (self.channel_ids) and (len(self.channel_ids)>0):
      R0=si.SubRecordingExtractor(parent_recording=R0,channel_ids=self.channel_ids)
    
    recording = R0
    # recording=sw.lazyfilters.bandpass_filter(recording=R0,freq_min=300,freq_max=6000)

    sorting=si.MdaSortingExtractor(firings_file=self.firings)
    unit_ids=self.unit_ids
    if (not unit_ids) or (len(unit_ids)==0):
      unit_ids=sorting.getUnitIds()
  
    channel_noise_levels=compute_channel_noise_levels(recording=recording)

    # No longer use subset to compute the templates
    templates=compute_unit_templates(recording=recording,sorting=sorting,unit_ids=unit_ids,max_num=100)

    ret=[]
    for i,unit_id in enumerate(unit_ids):
      template=templates[i]
      max_p2p_amps_on_channels=np.max(template,axis=1)-np.min(template,axis=1)
      peak_channel_index=np.argmax(max_p2p_amps_on_channels)
      peak_channel=recording.getChannelIds()[peak_channel_index]
      R1=si.SubRecordingExtractor(parent_recording=recording,channel_ids=[peak_channel_index])
      R1f=sw.lazyfilters.bandpass_filter(recording=R1,freq_min=300,freq_max=6000)
      templates2=compute_unit_templates(recording=R1f,sorting=sorting,unit_ids=[unit_id],max_num=100)
      template2=templates2[0]
      info0=dict()
      info0['unit_id']=int(unit_id)
      info0['snr']=np.max(np.abs(template2))/channel_noise_levels[peak_channel_index]
      #info0['snr']=compute_template_snr(template,channel_noise_levels)
      #peak_channel_index=np.argmax(np.max(np.abs(template),axis=1))
      info0['peak_channel']=int(recording.getChannelIds()[peak_channel])
      train=sorting.getUnitSpikeTrain(unit_id=unit_id)
      info0['num_events']=int(len(train))
      info0['firing_rate']=float(len(train)/(recording.getNumFrames()/recording.getSamplingFrequency()))
      ret.append(info0)
    write_json_file(self.json_out,ret)
  
  
## return format can be 'json' or 'filename'
def compute_units_info(*,recording_dir,firings,channel_ids=[],unit_ids=[],return_format='json'):
    out=ComputeUnitsInfo.execute(
      recording_dir=recording_dir,
      firings=firings,
      unit_ids=unit_ids,
      channel_ids=channel_ids,
      json_out={'ext':'.json'},
      _container='default'
    ).outputs
    fname=out['json_out']
    if return_format=='filename':
      return fname
    else:
      fname=ca.realizeFile(path=fname)
      with open(fname) as f:
        return json.load(f)

def select_units_on_channels(recording_dir,firings,channels):
  info=compute_units_info(recording_dir=recording_dir,firings=firings)
  units=[]
  for info0 in info:
    if info0['peak_channel'] in channels:
      units.append(info0['unit_id'])
  return units

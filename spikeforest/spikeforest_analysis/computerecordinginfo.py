from spikeforest import spikeextractors as si
import mlprocessors as mlpr
import json

try:
    # if we are running this outside the container
    from spikeforest import spikeextractors as si
except:
    # if we are in the container
    import spikeextractors as si

_CONTAINER='sha1://87319c2856f312ccc3187927ae899d1d67b066f9/03-20-2019/mountaintools_basic.simg'


# A MountainLab processor for generating the summary info for a recording
class ComputeRecordingInfo(mlpr.Processor):
  NAME='ComputeRecordingInfo'
  VERSION='0.1.1'
  CONTAINER=_CONTAINER

  recording_dir=mlpr.Input(directory=True,description='Recording directory')
  channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
  json_out=mlpr.Output('Info in .json file')
    
  def run(self):
    ret={}
    recording=si.MdaRecordingExtractor(dataset_directory=self.recording_dir,download=True)
    if len(self.channels)>0:
      recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
    ret['samplerate']=recording.getSamplingFrequency()
    ret['num_channels']=len(recording.getChannelIds())
    ret['duration_sec']=recording.getNumFrames()/ret['samplerate']
    write_json_file(self.json_out,ret)

def write_json_file(fname,obj):
  with open(fname, 'w') as f:
    json.dump(obj, f)

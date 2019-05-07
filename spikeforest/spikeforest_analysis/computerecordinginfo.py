import mlprocessors as mlpr
import json

import spikeextractors as si
from .sfmdaextractors import SFMdaRecordingExtractor, SFMdaSortingExtractor

_CONTAINER = 'sha1://5627c39b9bd729fc011cbfce6e8a7c37f8bcbc6b/spikeforest_basic.simg'


# A MountainLab processor for generating the summary info for a recording
class ComputeRecordingInfo(mlpr.Processor):
    NAME = 'ComputeRecordingInfo'
    VERSION = '0.1.1'
    CONTAINER = _CONTAINER

    recording_dir = mlpr.Input(directory=True, description='Recording directory')
    channels = mlpr.IntegerListParameter(description='List of channels to use.', optional=True, default=[])
    json_out = mlpr.Output('Info in .json file')

    def run(self):
        ret = {}
        recording = SFMdaRecordingExtractor(dataset_directory=self.recording_dir, download=True)
        if len(self.channels) > 0:
            recording = si.SubRecordingExtractor(parent_recording=recording, channel_ids=self.channels)
        ret['samplerate'] = recording.get_sampling_frequency()
        ret['num_channels'] = len(recording.get_channel_ids())
        ret['duration_sec'] = recording.get_num_frames() / ret['samplerate']
        write_json_file(self.json_out, ret)


def write_json_file(fname, obj):
    with open(fname, 'w') as f:
        json.dump(obj, f)

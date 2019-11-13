from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor, mdaio
from spikeforest_analysis import bandpass_filter
import mlprocessors as mlpr
from mountaintools import client as mt
import numpy as np
import json

class FilterTimeseries(mlpr.Processor):
    NAME = 'FilterTimeseries'
    VERSION = '0.1.0'
    CONTAINER = None

    recording_directory = mlpr.Input(description='Recording directory', optional=False, directory=True)
    timeseries_out = mlpr.Output(description='Filtered timeseries file (.mda)')

    def run(self):
        rx = SFMdaRecordingExtractor(dataset_directory=self.recording_directory, download=True)
        rx2 = bandpass_filter(recording=rx, freq_min=300, freq_max=6000, freq_wid=1000)
        if not mdaio.writemda32(rx2.get_traces(), self.timeseries_out):
            raise Exception('Unable to write output file.')

class ComputeUnitDetail(mlpr.Processor):
    NAME = 'ComputeUnitDetail'
    VERSION = '0.1.0'
    CONTAINER = None

    recording_dir = mlpr.Input(description='Recording directory', optional=False, directory=True)
    firings = mlpr.Input(description='Input firings.mda file')
    unit_id = mlpr.IntegerParameter(description='Unit ID')
    json_out = mlpr.Output(description='Output .json file')

    def run(self):
        recording = SFMdaRecordingExtractor(dataset_directory=self.recording_directory, download=True)
        sorting = SFMdaSortingExtractor(firings_file=self.firings)
        waveforms0 = _get_random_spike_waveforms(recording=recording, sorting=sorting, unit=self.unit_id)
        channel_ids = recording.get_channel_ids()
        avg_waveform = np.median(waveforms0, axis=2)
        ret = dict(
            channel_ids = channel_ids,
            average_waveform = avg_waveform.tolist()
        )
        with open(self.json_out, 'w') as f:
            json.dump(ret, f)

def _get_random_spike_waveforms(*, recording, sorting, unit, max_num=50, channels=None, snippet_len=100):
    st = sorting.get_unit_spike_train(unit_id=unit)
    num_events = len(st)
    if num_events > max_num:
        event_indices = np.random.choice(
            range(num_events), size=max_num, replace=False)
    else:
        event_indices = range(num_events)

    spikes = recording.get_snippets(reference_frames=st[event_indices].astype(int), snippet_len=snippet_len,
                                    channel_ids=channels)
    if len(spikes) > 0:
        spikes = np.dstack(tuple(spikes))
    else:
        spikes = np.zeros((recording.get_num_channels(), snippet_len, 0))
    return spikes
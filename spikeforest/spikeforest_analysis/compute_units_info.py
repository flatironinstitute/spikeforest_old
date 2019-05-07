import numpy as np
import json
import mlprocessors as mlpr
from mountaintools import client as mt
import spikeextractors as si
from .bandpass_filter import bandpass_filter
from .sfmdaextractors import SFMdaRecordingExtractor
from .sfmdaextractors import SFMdaSortingExtractor

_CONTAINER = 'sha1://5627c39b9bd729fc011cbfce6e8a7c37f8bcbc6b/spikeforest_basic.simg'


def write_json_file(fname, obj):
    with open(fname, 'w') as f:
        json.dump(obj, f)


def get_random_spike_waveforms(*, recording, sorting, unit, snippet_len, max_num, channels=None):
    st = sorting.get_unit_spike_train(unit_id=unit)
    num_events = len(st)
    if num_events > max_num:
        event_indices = np.random.choice(range(num_events), size=max_num, replace=False)
    else:
        event_indices = range(num_events)

    spikes = recording.get_snippets(reference_frames=st[event_indices].astype(int), snippet_len=snippet_len, channel_ids=channels)
    if len(spikes) > 0:
        spikes = np.dstack(tuple(spikes))
    else:
        spikes = np.zeros((recording.get_num_channels(), snippet_len, 0))
    return spikes


def compute_unit_templates(*, recording, sorting, unit_ids, snippet_len=50, max_num=100, channels=None):
    ret = []
    for unit in unit_ids:
        # print('Unit {} of {}'.format(unit,len(unit_ids)))
        waveforms = get_random_spike_waveforms(recording=recording, sorting=sorting, unit=unit, snippet_len=snippet_len, max_num=max_num, channels=None)
        template = np.median(waveforms, axis=2)
        ret.append(template)
    return ret


def compute_template_snr(template, channel_noise_levels):
    channel_snrs = []
    for ch in range(template.shape[0]):
        # channel_snrs.append((np.max(template[ch,:])-np.min(template[ch,:]))/channel_noise_levels[ch])
        channel_snrs.append((np.max(np.abs(template[ch, :]))) / channel_noise_levels[ch])
    return float(np.max(channel_snrs))


def compute_channel_noise_levels(recording):
    channel_ids = recording.get_channel_ids()
    # M=len(channel_ids)
    samplerate = int(recording.get_sampling_frequency())
    X = recording.get_traces(start_frame=samplerate * 1, end_frame=samplerate * 2)
    ret = []
    for ii in range(len(channel_ids)):
        # noise_level=np.std(X[ii,:])
        noise_level = np.median(np.abs(X[ii, :])) / 0.6745  # median absolute deviation (MAD)
        ret.append(noise_level)
    return ret


class ComputeUnitsInfo(mlpr.Processor):
    NAME = 'ComputeUnitsInfo'
    VERSION = '0.1.8'
    CONTAINER = _CONTAINER
    recording_dir = mlpr.Input(directory=True, description='Recording directory')
    channel_ids = mlpr.IntegerListParameter(description='List of channels to use.', optional=True, default=[])
    unit_ids = mlpr.IntegerListParameter(description='List of units to use.', optional=True, default=[])
    firings = mlpr.Input(description='Firings file')
    json_out = mlpr.Output('The info as a .json file')

    def run(self):
        R0 = SFMdaRecordingExtractor(dataset_directory=self.recording_dir, download=True)
        sorting = SFMdaSortingExtractor(firings_file=self.firings)
        ret = compute_units_info(recording=R0, sorting=sorting, channel_ids=self.channel_ids, unit_ids=self.unit_ids)
        write_json_file(self.json_out, ret)


def compute_units_info(*, recording, sorting, channel_ids=[], unit_ids=[]):
    if (channel_ids) and (len(channel_ids) > 0):
        recording = si.SubRecordingExtractor(parent_recording=recording, channel_ids=channel_ids)

    # load into memory
    print('Loading recording into RAM...')
    recording = si.NumpyRecordingExtractor(timeseries=recording.get_traces(), samplerate=recording.get_sampling_frequency())

    # do filtering
    print('Filtering...')
    recording = bandpass_filter(recording=recording, freq_min=300, freq_max=6000)
    recording = si.NumpyRecordingExtractor(timeseries=recording.get_traces(), samplerate=recording.get_sampling_frequency())

    if (not unit_ids) or (len(unit_ids) == 0):
        unit_ids = sorting.get_unit_ids()

    print('Computing channel noise levels...')
    channel_noise_levels = compute_channel_noise_levels(recording=recording)

    # No longer use subset to compute the templates
    print('Computing unit templates...')
    templates = compute_unit_templates(recording=recording, sorting=sorting, unit_ids=unit_ids, max_num=100)

    print(recording.get_channel_ids())

    ret = []
    for i, unit_id in enumerate(unit_ids):
        print('Unit {} of {} (id={})'.format(i + 1, len(unit_ids), unit_id))
        template = templates[i]
        max_p2p_amps_on_channels = np.max(template, axis=1) - np.min(template, axis=1)
        peak_channel_index = np.argmax(max_p2p_amps_on_channels)
        peak_channel = recording.get_channel_ids()[peak_channel_index]
        peak_signal = np.max(np.abs(template[peak_channel_index, :]))
        info0 = dict()
        info0['unit_id'] = int(unit_id)
        info0['snr'] = peak_signal / channel_noise_levels[peak_channel_index]
        info0['peak_channel'] = int(recording.get_channel_ids()[peak_channel])
        train = sorting.get_unit_spike_train(unit_id=unit_id)
        info0['num_events'] = int(len(train))
        info0['firing_rate'] = float(len(train) / (recording.get_num_frames() / recording.get_sampling_frequency()))
        ret.append(info0)
    return ret


# return format can be 'json' or 'filename'
def compute_units_info_b(*, recording_dir, firings, channel_ids=[], unit_ids=[], return_format='json'):
    out = ComputeUnitsInfo.execute(
        recording_dir=recording_dir,
        firings=firings,
        unit_ids=unit_ids,
        channel_ids=channel_ids,
        json_out={'ext': '.json'},
        _container='default'
    ).outputs
    fname = out['json_out']
    if return_format == 'filename':
        return fname
    else:
        fname = mt.realizeFile(path=fname)
        with open(fname) as f:
            return json.load(f)


def select_units_on_channels(recording_dir, firings, channels):
    info = compute_units_info_b(recording_dir=recording_dir, firings=firings)
    units = []
    for info0 in info:
        if info0['peak_channel'] in channels:
            units.append(info0['unit_id'])
    return units

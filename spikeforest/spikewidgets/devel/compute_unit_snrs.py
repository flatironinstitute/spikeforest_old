import numpy as np


def get_random_spike_waveforms(*, recording, sorting, unit, snippet_len, max_num, channels=None):
    st = sorting.getUnitSpikeTrain(unit_id=unit)
    num_events = len(st)
    if num_events > max_num:
        event_indices = np.random.choice(range(num_events), size=max_num, replace=False)
    else:
        event_indices = range(num_events)

    spikes = recording.getSnippets(reference_frames=st[event_indices].astype(int), snippet_len=snippet_len,
                                   channel_ids=channels)
    spikes = np.dstack(tuple(spikes))
    return spikes


def compute_unit_templates(*, recording, sorting, unit_ids, snippet_len=50):
    ret = []
    for unit in unit_ids:
        waveforms = get_random_spike_waveforms(recording=recording, sorting=sorting, unit=unit, snippet_len=snippet_len,
                                               max_num=200)
        template = np.mean(waveforms, axis=2)
        ret.append(template)
    return ret


def compute_template_snr(template, channel_noise_levels):
    channel_snrs = []
    for ch in range(template.shape[0]):
        channel_snrs.append((np.max(template[ch, :]) - np.min(template[ch, :])) / channel_noise_levels[ch])
    return np.max(channel_snrs)


def compute_channel_noise_levels(recording):
    channel_ids = recording.getChannelIds()
    M = len(channel_ids)
    X = recording.getTraces(start_frame=0, end_frame=np.minimum(1000, recording.getNumFrames()))
    ret = []
    for ii in len(channel_ids):
        noise_level = np.std(X[ii, :])
        ret.append(noise_level)
    return ret


def compute_unit_snrs(*, recording, sorting, unit_ids=None):
    if unit_ids is None:
        unit_ids = sorting.getUnitIds()
    channel_noise_levels = compute_channel_noise_levels(recording=recording)
    templates = compute_unit_templates(recording=recording, sorting=sorting, unit_ids=unit_ids)
    ret = []
    for template in templates:
        snr = compute_template_snr(template, channel_noise_levels)
        ret.append(snr)
    return ret

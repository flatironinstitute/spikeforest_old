from .bandpass_filter import bandpass_filter
import spikeextractors as se
import numpy as np


def estimateRecordingNoiseLevel(recording):
    return _estimate_noise_level(recording)


def autoScaleRecordingToNoiseLevel(recording, noise_level):
    noise_level_est = _estimate_noise_level(recording)
    return _scale_recording(recording, noise_level / noise_level_est)


def _estimate_channel_noise_levels_helper(recording):
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


def _estimate_channel_noise_levels(recording):
    recording_filtered = bandpass_filter(recording=recording, freq_min=200, freq_max=30000)
    return _estimate_channel_noise_levels_helper(recording=recording_filtered)


def _estimate_noise_level(recording):
    return np.median(_estimate_channel_noise_levels(recording))


class ScaledRecording(se.RecordingExtractor):
    def __init__(self, recording, scalar=1):
        se.RecordingExtractor.__init__(self)
        if not isinstance(recording, se.RecordingExtractor):
            raise ValueError("'recording' must be a RecordingExtractor")
        self._recording = recording
        self._scalar = scalar
        self.copy_channel_properties(recording=self._recording)

    def get_sampling_frequency(self):
        return self._recording.get_sampling_frequency()

    def get_num_frames(self):
        return self._recording.get_num_frames()

    def get_channel_ids(self):
        return self._recording.get_channel_ids()

    def get_traces(self, channel_ids=None, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = self.get_num_frames()
        if channel_ids is None:
            channel_ids = self.get_channel_ids()
        traces = self._recording.get_traces(channel_ids=channel_ids, start_frame=start_frame, end_frame=end_frame)
        return traces * self._scalar


def _scale_recording(recording, scalar=1):
    return ScaledRecording(
        recording=recording, scalar=scalar
    )


def _compute_recording_range(recording):
    all_traces = recording.get_traces()
    return [np.min(all_traces), np.max(all_traces)]

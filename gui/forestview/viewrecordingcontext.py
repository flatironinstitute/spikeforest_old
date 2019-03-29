from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
from copy import deepcopy

class ViewRecordingContext():
    def __init__(self, recording_object):
        self._recording_object = recording_object
        self._rx = SFMdaRecordingExtractor(dataset_directory = self._recording_object['directory'])
        self._state = dict(
            current_timepoint = None,
            selected_time_range = None
        )
        self._signal_handlers = dict()

    def recordingObject(self):
        return self._recording_object

    def studyName(self):
        return self._recording_object.get('study', '')

    def recordingName(self):
        return self._recording_object.get('name', '')

    def recordingDirectory(self):
        return self._recording_object.get('directory', '')

    def recordingExtractor(self):
        return self._rx

    # current timepoint
    def setCurrentTimepoint(self, tp):
        self._set_state_value('current_timepoint', tp)

    def currentTimepoint(self):
        return self._get_state_value('current_timepoint')

    def onCurrentTimepointChanged(self, handler):
        self._register_state_change_handler('current_timepoint', handler)

    # current time range
    def setCurrentTimeRange(self, range):
        self._set_state_value('current_time_range', range)

    def currentTimeRange(self):
        return self._get_state_value('current_time_range')

    def onCurrentTimeRangeChanged(self, handler):
        self._register_state_change_handler('current_time_range', handler)

    def _set_state_value(self, name, val):
        if self._state[name] == val:
            return
        self._state[name] = deepcopy(val)
        self._emit('state-changed-'+name)

    def _get_state_value(self, name):
        return deepcopy(self._state[name])

    def _register_state_change_handler(self, name, handler):
        self._register_signal_handler('state-changed-'+name, handler)

    def _register_signal_handler(self, signal_name, handler):
        if signal_name not in self._signal_handlers:
            self._signal_handlers[signal_name] = []
        self._signal_handlers[signal_name].append(handler)

    def _emit(self, signal_name):
        if signal_name in self._signal_handlers:
            for handler in self._signal_handlers[signal_name]:
                handler()

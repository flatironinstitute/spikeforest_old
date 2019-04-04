from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor, EfficientAccessRecordingExtractor
from copy import deepcopy
import spikeforestwidgets as SFW
from mountaintools import client as mt

class ViewRecordingContext():
    def __init__(self, recording_object, *, download=True, create_earx=True, precompute_multiscale=True):
        self._signal_handlers = dict()
        
        self._current_channel = -1
        
        print('******** FORESTVIEW: Initializing recording context')
        self._recording_object = recording_object
        if download:
            print('******** FORESTVIEW: Downloading recording file if needed...')
        recdir = self._recording_object['directory']
        self._rx = SFMdaRecordingExtractor(dataset_directory = recdir, download=download)

        firings_true_path = recdir + '/firings_true.mda'
        self._sx = None
        if mt.findFile(path=firings_true_path):
            print('******** FORESTVIEW: Downloading true firings file if needed...')
            if not mt.realizeFile(firings_true_path):
                print('Warning: unable to realize true firings file: '+firings_true_path)
            else:
                self._sx = SFMdaSortingExtractor(firings_file = firings_true_path)

        print('******** FORESTVIEW: Done initializing recording context')
        self._state = dict(
            current_timepoint = None,
            selected_time_range = None,
            current_channel = None
        )

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

    def sortingExtractor(self):
        return self._sx

    def currentChannel(self):
        return self._get_state_value('current_channel')

    def setCurrentChannel(self, ch):
        self._set_state_value('current_channel', ch)

    def onCurrentChannelChanged(self, handler):
        self._register_state_change_handler('current_channel', handler)

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

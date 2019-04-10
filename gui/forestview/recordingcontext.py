from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor, EfficientAccessRecordingExtractor
from copy import deepcopy
import spikeforestwidgets as SFW
from mountaintools import client as mt
from bandpass_filter import bandpass_filter

class RecordingContext():
    def __init__(self, recording_object, *, download=True, create_earx=True, precompute_multiscale=True):
        self._signal_handlers = dict()
        self._recording_object = recording_object
        self._download = download

        self._state = dict(
            current_timepoint = None,
            selected_time_range = None,
            current_channel = None,
            current_unit_id = None,
            selected_unit_ids = []
        )

        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        
        print('******** FORESTVIEW: Initializing recording context')
        self._recording_object = self._recording_object
        if self._download:
            print('******** FORESTVIEW: Downloading recording file if needed...')
        recdir = self._recording_object['directory']
        self._rx = SFMdaRecordingExtractor(dataset_directory = recdir, download=self._download)
        self._rx = bandpass_filter(self._rx)

        firings_true_path = recdir + '/firings_true.mda'
        self._sx = None
        if mt.findFile(path=firings_true_path):
            print('******** FORESTVIEW: Downloading true firings file if needed...')
            if not mt.realizeFile(firings_true_path):
                print('Warning: unable to realize true firings file: '+firings_true_path)
            else:
                self._sx = SFMdaSortingExtractor(firings_file = firings_true_path)

        print('******** FORESTVIEW: Done initializing recording context')

    def recordingObject(self):
        return deepcopy(self._recording_object)

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

    def onAnyStateChanged(self, handler):
        for key in self._state.keys():
            self._register_state_change_handler(key, handler)

    def stateObject(self):
        return deepcopy(self._state)

    # current channel
    def currentChannel(self):
        return self._get_state_value('current_channel')

    def setCurrentChannel(self, ch):
        ch=int(ch)
        self._set_state_value('current_channel', ch)

    def onCurrentChannelChanged(self, handler):
        self._register_state_change_handler('current_channel', handler)

    # current timepoint
    def setCurrentTimepoint(self, tp):
        tp = int(tp)
        self._set_state_value('current_timepoint', tp)

    def currentTimepoint(self):
        return self._get_state_value('current_timepoint')

    def onCurrentTimepointChanged(self, handler):
        self._register_state_change_handler('current_timepoint', handler)

    # current time range
    def setCurrentTimeRange(self, range):
        range=(int(range[0]), int(range[1]))
        self._set_state_value('current_time_range', range)

    def currentTimeRange(self):
        return self._get_state_value('current_time_range')

    def onCurrentTimeRangeChanged(self, handler):
        self._register_state_change_handler('current_time_range', handler)

    # current unit ID
    def setCurrentUnitId(self, unit_id):
        unit_id = int(unit_id)
        self._set_state_value('current_unit_id', unit_id)

    def currentUnitId(self):
        return self._get_state_value('current_unit_id')

    def onCurrentUnitIdChanged(self, handler):
        self._register_state_change_handler('current_unit_id', handler)

    # selected unit IDs
    def setSelectedUnitIds(self, unit_ids):
        if unit_ids is None:
            unit_ids=[]
        unit_ids = sorted([int(id) for id in unit_ids])
        self._set_state_value('selected_unit_ids', sorted(unit_ids))

    def selectedUnitIds(self):
        return self._get_state_value('selected_unit_ids')

    def onSelectedUnitIdsChanged(self, handler):
        self._register_state_change_handler('selected_unit_ids', handler)

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

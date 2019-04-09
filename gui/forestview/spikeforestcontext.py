from copy import deepcopy
from mountaintools import client as mt
from spikeforest import SFMdaRecordingExtractor
from mountaintools import MountainClient

local_client = MountainClient()

class SpikeForestContext():
    def __init__(self, studies=[], recordings=[]):
        self._signal_handlers = dict()
        
        print('******** FORESTVIEW: Initializing study context')
        self._studies = studies
        self._recordings = recordings

        self._studies_by_name = dict()
        for stu in self._studies:
            self._studies_by_name[stu['name']] = stu

        self._recordings_by_id = dict()
        for rec in self._recordings:
            self._recordings_by_id[rec['study']+'/'+rec['name']] = rec

        print('******** FORESTVIEW: Done initializing study context')
        self._state = dict(
            current_recording_id = None,
            selected_recording_ids = []
        )

    def studyNames(self):
        return sorted(list())

    def recordingIds(self):
        return sorted(list(self._recordings_by_id.keys()))

    def recordingObject(self, recid):
        return deepcopy(self._recordings_by_id[recid])

    # def recordingExtractor(self, recording_name, *, download):
    #     print('loading recording extractor....', recording_name, download)
    #     return SFMdaRecordingExtractor(self._study_dir + '/' + recording_name, download=download)

    def onAnyStateChanged(self, handler):
        for key in self._state.keys():
            self._register_state_change_handler(key, handler)

    def stateObject(self):
        return deepcopy(self._state)

    # current recording
    def currentRecordingId(self):
        return self._get_state_value('current_recording_id')

    def setCurrentRecordingId(self, recname):
        self._set_state_value('current_recording_id', recname)

    def onCurrentRecordingChanged(self, handler):
        self._register_state_change_handler('current_recording_id', handler)

    # selected recordings
    def setSelectedRecordingIds(self, recids):
        if recids is None:
            recids=[]
        recids = sorted(recids)
        self._set_state_value('selected_recording_ids', recids)

    def selectedRecordingIds(self):
        return self._get_state_value('selected_recording_ids')

    def onSelectedRecordingsChanged(self, handler):
        self._register_state_change_handler('selected_recording_ids', handler)

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

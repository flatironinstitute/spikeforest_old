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
        self._recordings_by_id = dict()
        for rec in self._recordings:
            self._recordings_by_id[rec['study']+'/'+rec['name']] = rec

        print('******** FORESTVIEW: Done initializing study context')
        self._state = dict(
            current_recording_id = None,
            selected_recording_ids = []
        )

    def studyNames(self):
        return [study['name'] for study in self._studies]

    def recordingIds(self):
        return sorted(list(self._recordings_by_id.keys()))

    def recordingInfo(self, recording_name):
        recdir = self._study_dir+'/'+recording_name
        timeseries_fname = recdir+'/raw.mda'
        geom_fname = recdir+'/geom.csv'
        timeseries_fname = local_client.realizeFile(timeseries_fname)
        geom_fname = local_client.realizeFile(geom_fname)
        ret = dict()
        mt.realizeFile()

    def recordingExtractor(self, recording_name, *, download):
        print('loading recording extractor....', recording_name, download)
        return SFMdaRecordingExtractor(self._study_dir + '/' + recording_name, download=download)

    def onAnyStateChanged(self, handler):
        for key in self._state.keys():
            self._register_state_change_handler(key, handler)

    def stateObject(self):
        return deepcopy(self._state)

    # current recording
    def currentRecordingName(self):
        return self._get_state_value('current_recording')

    def setCurrentRecordingName(self, recname):
        self._set_state_value('current_recording', recname)

    def onCurrentRecordingChanged(self, handler):
        self._register_state_change_handler('current_recording', handler)

    # selected recordings
    def setSelectedRecordingNames(self, recnames):
        if recnames is None:
            recnames=[]
        recnames = sorted(recnames)
        self._set_state_value('selected_recordings', recnames)

    def selectedRecordingNames(self):
        return self._get_state_value('selected_recordings')

    def onSelectedRecordingsChanged(self, handler):
        self._register_state_change_handler('selected_recordings', handler)

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

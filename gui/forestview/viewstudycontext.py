from copy import deepcopy
from mountaintools import client as mt

class ViewStudyContext():
    def __init__(self, study_object):
        self._signal_handlers = dict()
        
        print('******** FORESTVIEW: Initializing study context')
        self._study_object = study_object
        studydir = self._study_object['directory']
        dd = mt.readDir(studydir)
        self._recording_names = []
        for recname in dd['dirs']:
            print(recname)
            self._recording_names.append(recname)

        print('******** FORESTVIEW: Done initializing study context')
        self._state = dict(
            current_recording = None,
            selected_recordings = []
        )

    def studyObject(self):
        return deepcopy(self._study_object)

    def studyName(self):
        return self._study_object.get('name', '')

    def studyDirectory(self):
        return self._study_object.get('directory', '')

    def recordingNames(self):
        return self._recording_names

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

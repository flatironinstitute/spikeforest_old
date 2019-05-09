from copy import deepcopy
from mountaintools import client as mt
from spikeforest import SFMdaRecordingExtractor
from .spikefront_view_launchers import get_spikefront_view_launchers
from .recordingcontext import RecordingContext


class SpikeFrontContext():
    def __init__(
        self,
        StudySets=[], Recordings=[],
        TrueUnits=[], UnitResults=[],
        SortingResults=[], Sorters=[],
        Studies=[], Algorithms=[],
        StudyAnalysisResults=[]
    ):
        self._signal_handlers = dict()
        self._any_state_change_handlers = []

        print('******** FORESTVIEW (spike-front): Initializing context')
        self._StudySets = StudySets
        self._Recordings = Recordings
        self._TrueUnits = TrueUnits
        self._SortingResults = SortingResults
        self._Sorters = Sorters
        self._Studies = Studies
        self._Algorithms = Algorithms
        self._StudyAnalysisResults = StudyAnalysisResults

        self._study_sets_by_name = dict()
        for x in self._StudySets:
            self._study_sets_by_name[x['name']] = x

        self._studies_by_name = dict()
        for x in self._Studies:
            self._studies_by_name[x['name']] = x

        self._study_analysis_results_by_name = dict()
        for x in self._StudyAnalysisResults:
            self._study_analysis_results_by_name[x['studyName']] = x

        self._sorters_by_name = dict()
        for x in self._Sorters:
            self._sorters_by_name[x['name']] = x

        # self._recording_contexts = dict()
        self._recordings_by_id = dict()
        for rec in self._Recordings:
            id0 = rec['study'] + '/' + rec['name']
            self._recordings_by_id[id0] = rec
            # c0 = RecordingContext(rec)
            # c0.onAnyStateChanged(self._trigger_any_state_change_handlers)
            # self._recording_contexts[id0] = c0

        print('******** FORESTVIEW (spike-front): Done initializing context')
        self._state = dict(
            current_study_name=None
        )

    def viewLaunchers(self):
        return get_spikefront_view_launchers(self)

    def studySetNames(self):
        return sorted(list(self._study_sets_by_name.keys()))

    def studySetObject(self, name):
        return deepcopy(self._study_sets_by_name.get(name, {}))

    def studyNames(self):
        return sorted(list(self._studies_by_name.keys()))

    def studyObject(self, name):
        return deepcopy(self._studies_by_name.get(name, {}))

    def studySetObjectForStudy(self, name):
        return self.studySetObject(self.studyObject(name).get('studySetName'))

    def recordingIds(self):
        return sorted(list(self._recordings_by_id.keys()))

    def recordingObject(self, recid):
        return deepcopy(self._recordings_by_id[recid])

    def sorterNames(self):
        return sorted(list(self._sorters_by_name.keys()))

    def sorterObject(self, name):
        return deepcopy(self._sorters_by_name[name])

    def studyAnalysisResultObject(self, name):
        return deepcopy(self._study_analysis_results_by_name.get(name, {}))

    def onAnyStateChanged(self, handler):
        for key in self._state.keys():
            self._register_state_change_handler(key, handler)
        self._any_state_change_handlers.append(handler)

    def stateObject(self):
        ret = deepcopy(self._state)
        return ret

    # current study
    def currentStudyName(self):
        return self._get_state_value('current_study_name')

    def setCurrentStudyName(self, name):
        self._set_state_value('current_study_name', name)

    def onCurrentStudyChanged(self, handler):
        self._register_state_change_handler('current_study_name', handler)

    def _set_state_value(self, name, val):
        if self._state[name] == val:
            return
        self._state[name] = deepcopy(val)
        self._emit('state-changed-' + name)

    def _get_state_value(self, name):
        return deepcopy(self._state[name])

    def _register_state_change_handler(self, name, handler):
        self._register_signal_handler('state-changed-' + name, handler)

    def _register_signal_handler(self, signal_name, handler):
        if signal_name not in self._signal_handlers:
            self._signal_handlers[signal_name] = []
        self._signal_handlers[signal_name].append(handler)

    def _emit(self, signal_name):
        if signal_name in self._signal_handlers:
            for handler in self._signal_handlers[signal_name]:
                handler()

    def _trigger_any_state_change_handlers(self):
        for handler in self._any_state_change_handlers:
            handler()

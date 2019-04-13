from copy import deepcopy
from mountaintools import client as mt
from mountaintools import MountainClient
from .analysis_view_launchers import get_analysis_view_launchers

local_client = MountainClient()

class AnalysisContext():
    def __init__(self, obj):
        self._object = obj
        self._o = self._object # for convenience
        self._any_state_change_handlers = []
        self._signal_handlers = dict()

        print('******** FORESTVIEW: Done initializing study context')
        self._state = dict(
            current_sorter = None
        )

    def initialize(self):
        pass

    def analysisName(self):
        return self._o.get('analysis_name', None)

    def outputPath(self):
        return self._o.get('output', None)

    def recordingGroups(self):
        return self._o.get('recordings', [])

    def sorterKeys(self):
        return self._o.get('sorter_keys', [])

    def downloadFrom(self):
        return self._o.get('download_from', [])

    def jobTimeout(self):
        return self._o.get('job_timeout', None)

    def computeResourceKeys(self):
        return self._o.get('compute_resources', dict()).keys()

    def sorterDefinitionKeys(self):
        return self._o.get('sorters', dict()).keys()
    
    def sorterDefinition(self, key):
        return self._o.get('sorters', dict()).get(key)

    def viewLaunchers(self):
        return get_analysis_view_launchers(self)

    def onAnyStateChanged(self, handler):
        for key in self._state.keys():
            self._register_state_change_handler(key, handler)
        self._any_state_change_handlers.append(handler)

    def stateObject(self):
        ret = deepcopy(self._state)
        return ret

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

    def _trigger_any_state_change_handlers(self):
        for handler in self._any_state_change_handlers:
            handler()

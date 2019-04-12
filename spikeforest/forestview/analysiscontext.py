from copy import deepcopy
from mountaintools import client as mt
from mountaintools import MountainClient

local_client = MountainClient()

class AnalysisContext():
    def __init__(self, object):
        self._object = object
        self._any_state_change_handlers = []
        self._signal_handlers = dict()

        print('******** FORESTVIEW: Done initializing study context')
        self._state = dict(
            current_sorter = None
        )

    def viewLaunchers(self):
        # return get_spikeforest_view_launchers(self)
        return dict(
            groups=[],
            launchers=[]
        )

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

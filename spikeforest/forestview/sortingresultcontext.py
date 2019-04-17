from spikeforest import SFMdaSortingExtractor
from copy import deepcopy
from mountaintools import client as mt
from .recordingcontext import RecordingContext
import mtlogging

class SortingResultContext():
    def __init__(self, *, sorting_result_object, recording_context):
        self._signal_handlers = dict()
        self._sorting_result_object = sorting_result_object
        self._recording_context = recording_context
        
        self._state = dict(
            current_unit_id = None,
            selected_unit_ids = []
        )

        self._initialized = False

    @mtlogging.log(name='SortingResultContext:initialize', root=True)
    def initialize(self):
        if self._initialized:
            return
        self._initialized = True

        self._recording_context.initialize()

        print('******** FORESTVIEW: Initializing sorting result context')
        
        if self._sorting_result_object['firings']:
            self._sorting_extractor = SFMdaSortingExtractor(firings_file =self._sorting_result_object['firings'])
        else:
            self._sorting_extractor = None

        print('******** FORESTVIEW: Done initializing sorting result context')

    def sortingResultObject(self):
        return deepcopy(self._sorting_result_object)

    def sortingLabel(self):
        # MEDIUM TODO fill in details of sorting label here
        return 'Sorting'

    def recordingContext(self):
        return self._recording_context

    def sortingExtractor(self):
        return self._sorting_extractor

    def onAnyStateChanged(self, handler):
        for key in self._state.keys():
            self._register_state_change_handler(key, handler)

    def stateObject(self, *, include_recording=True):
        ret = deepcopy(self._state)
        if include_recording:
            ret['recording'] = self.recordingContext().stateObject()
        return ret

    def consoleOutputPath(self):
        return self._sorting_result_object.get('console_out', None)

    def executionStats(self):
        return self._sorting_result_object.get('execution_stats', None)

    def comparisonWithTruthPath(self):
        return (self._sorting_result_object.get('comparison_with_truth', {}) or {}).get('json', None)

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

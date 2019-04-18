from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor, EfficientAccessRecordingExtractor
from copy import deepcopy
import spikeforestwidgets as SFW
from mountaintools import client as mt
from .bandpass_filter import bandpass_filter

class RecordingContext():
    def __init__(self, recording_object, *, download=True, create_earx=True, precompute_multiscale=True):
        from .sortingresultcontext import SortingResultContext # avoid cyclic dependency

        self._signal_handlers = dict()
        self._any_state_change_handlers = []
        self._recording_object = recording_object
        self._download = download

        self._sorting_result_contexts = dict()
        
        if 'firings_true' in recording_object:
            sc_true = SortingResultContext(sorting_result_object=dict(firings=recording_object['firings_true']), recording_context=self)
            self._true_sorting_context = sc_true
            sc_true.onAnyStateChanged(self._trigger_any_state_change_handlers)
        else:
            self._true_sorting_context = None

        if self._recording_object.get('intra_recording', None):
            self._intra_recording_context = RecordingContext(recording_object=self._recording_object['intra_recording'], download=download, create_earx=create_earx, precompute_multiscale=precompute_multiscale)
        else:
            self._intra_recording_context = None

        self._state = dict(
            current_timepoint = None,
            selected_time_range = None,
            current_channel = None,
            current_sorting_result = None
        )

        self._initialized = False

    def initialize(self):
        if self._initialized:
            return
        self._initialized = True
        
        print('******** FORESTVIEW: Initializing recording context')
        self._recording_object = self._recording_object
        if self._download:
            print('******** FORESTVIEW: Downloading recording file if needed...')
        recdir = self._recording_object['directory']
        raw_fname = self._recording_object.get('raw_fname', 'raw.mda')
        params_fname = self._recording_object.get('params_fname', 'params.json')
        self._rx = SFMdaRecordingExtractor(dataset_directory = recdir, download=self._download, raw_fname=raw_fname, params_fname=params_fname)
        self._rx = bandpass_filter(self._rx)

        if self._true_sorting_context:
            self._true_sorting_context.initialize()

        # firings_true_path = recdir + '/firings_true.mda'
        # self._sx_true = None
        # if mt.computeFileSha1(path=firings_true_path):
        #     print('******** FORESTVIEW: Downloading true firings file if needed...')
        #     if not mt.realizeFile(firings_true_path):
        #         print('Warning: unable to realize true firings file: '+firings_true_path)
        #     else:
        #         self._sx_true = SFMdaSortingExtractor(firings_file = firings_true_path)

        if self._intra_recording_context:
            self._intra_recording_context.initialize()

        print('******** FORESTVIEW: Done initializing recording context')

    def sortingResultNames(self):
        return sorted(list(self._sorting_result_contexts.keys()))

    def sortingResultContext(self, name):
        return self._sorting_result_contexts[name]

    def addSortingResult(self, sorting_result_object):
        from .sortingresultcontext import SortingResultContext # avoid cyclic dependency
        sc = SortingResultContext(sorting_result_object=sorting_result_object, recording_context=self)
        sc.onAnyStateChanged(self._trigger_any_state_change_handlers)
        self._sorting_result_contexts[sorting_result_object['sorter']['name']]=sc

    def recordingObject(self):
        return deepcopy(self._recording_object)

    def studyName(self):
        return self._recording_object.get('study', '')

    def recordingName(self):
        return self._recording_object.get('name', '')

    def recordingLabel(self):
        return '{}/{}'.format(self.studyName(), self.recordingName())

    def recordingDirectory(self):
        return self._recording_object.get('directory', '')

    def recordingExtractor(self):
        return self._rx

    def trueSortingContext(self):
        return self._true_sorting_context

    def intraRecordingContext(self):
        return self._intra_recording_context

    def hasIntraRecording(self):
        return self._intra_recording_context is not None

    def onAnyStateChanged(self, handler):
        for key in self._state.keys():
            self._register_state_change_handler(key, handler)
        self._any_state_change_handlers.append(handler)

    def stateObject(self):
        ret = deepcopy(self._state)
        sc = self.trueSortingContext()
        if sc:
            ret['true_sorting'] = sc.stateObject(include_recording=False)
        else:
            ret['true_sorting'] = None
        return ret

    # current channel
    def currentChannel(self):
        return self._get_state_value('current_channel')

    def setCurrentChannel(self, ch):
        if ch is not None:
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

    # current sorting result
    def currentSortingResult(self):
        return self._get_state_value('current_sorting_result')

    def setCurrentSortingResult(self, srname):
        self._set_state_value('current_sorting_result', srname)

    def onCurrentSortingResultChanged(self, handler):
        self._register_state_change_handler('current_sorting_result', handler)

    ###############################################

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

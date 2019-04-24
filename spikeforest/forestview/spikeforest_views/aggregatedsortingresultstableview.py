import vdomr as vd
import time
import sys
import mtlogging
import numpy as np
import json
from .tablewidget import TableWidget

class AggregatedSortingResultsTableView(vd.Component):
    def __init__(self, context, opts=None, prepare_result=None):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        self._aggregated_sorting_results = prepare_result.get('aggregated_sorting_results', None)
        self._table_widget = AggregatedSortingResultsTableWidget(context=context, aggregated_sorting_results=self._aggregated_sorting_results)
    
    # this will be done in a worker thread
    @staticmethod
    def prepareView(context, opts):
        # make sure it gets downloaded
        print('Loading aggregated sorting results...')
        aggregated_sorting_results = context.aggregatedSortingResults()

        return dict(
            aggregated_sorting_results=aggregated_sorting_results
        )
    
    def setSize(self, size):
        self._size=size
        if self._table_widget:
            self._table_widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Aggregated results table'
    def render(self):
        return vd.div(
            self._table_widget
        )

class AggregatedSortingResultsTableWidget(vd.Component):
    def __init__(self, *, context, aggregated_sorting_results):
        vd.Component.__init__(self)
        self._size = (100,100)
        self._context = context
        self._aggregated_sorting_results = aggregated_sorting_results
        self._asr = AggregatedSortingResults(self._aggregated_sorting_results)
        self._update_table()
    def setSize(self, size):
        self._size = size
        self._update_table()
    def _update_table(self):
        accuracy_thresh = 0.8
        study_names = self._asr.studyNames()
        sorter_names = self._asr.sorterNames()
        records = []
        for study_name in study_names:
            rec0 = dict(
                study_name=study_name
            )
            for sn in sorter_names:
                count0 = self._asr.getAccuracyCount(study_name=study_name, sorter_name=sn, accuracy_thresh=accuracy_thresh)
                if count0 is not None:
                    val0 = str(count0)
                else:
                    val0 = ''
                rec0['sorter-'+sn] = val0
            records.append(rec0)
        columns0 =  [
            dict(label=sorter_name, name='sorter-'+sorter_name)
            for sorter_name in sorter_names
        ]
        columns = [dict(label='Study', name='study_name')] + columns0
            
        self._table_widget = TableWidget(
            columns = columns,
            records = records,
            height=self._size[1]
        )
        self.refresh()

        # self._recording_ids = self._context.recordingIds()
        # recobjs = [self._context.recordingObject(recid) for recid in self._recording_ids]
        # records = [
        #     dict(
        #         study_name=obj['study'],
        #         recording_name=obj['name'],
        #         duration_sec=_get_computed_info(obj, 'duration_sec'),
        #         samplerate=_get_computed_info(obj, 'samplerate'),
        #         num_channels=_get_computed_info(obj, 'num_channels')
        #     )
        #     for obj in recobjs
        # ]

        # self._table_widget = TableWidget(
        #     columns = [
        #         dict(label='Study', name='study_name'),
        #         dict(label='Recording', name='recording_name'),
        #         dict(label='Duration (sec)', name='duration_sec'),
        #         dict(label='Sampling freq. (Hz)', name='samplerate'),
        #         dict(label='Num. channels', name='num_channels'),
        #     ],
        #     records = records,
        #     height=self._size[1]
        # )
        # self._table_widget.onSelectionChanged(self._on_widget_selection_changed)
        # self._on_context_selection_changed()
        # self.refresh()
    def _on_widget_selection_changed(self):
        current_row_index = self._table_widget.currentRowIndex()
        # if current_row_index is not None:
        #     self._context.setCurrentRecordingId(self._recording_ids[current_row_index])
        # else:
        #     self._context.setCurrentRecordingId(None)
    def _on_context_selection_changed(self):
        pass
        # recid = self._context.currentRecordingId()
        # if recid is not None:
        #     try:
        #         index0 = self._recording_ids.index(recid)
        #     except:
        #         index0 = None
        # else:
        #     index0 = None
        # self._table_widget.setCurrentRowIndex(index0)

    def render(self):
        return self._table_widget

class AggregatedSortingResults():
    def __init__(self, obj):
        self._obj = obj
        
        study_names = set()
        sorter_names = set()
        self._study_sorting_results_by_code = dict()
        for sr in obj.get('study_sorting_results', []):
            study0 = sr['study']
            sorter0 = sr['sorter']
            code0 = study0+'----'+sorter0
            study_names.add(study0)
            sorter_names.add(sorter0)
            self._study_sorting_results_by_code[code0] = sr
        
        self._study_names = sorted(list(study_names))
        self._sorter_names = sorted(list(sorter_names))

    def studyNames(self):
        return self._study_names
    
    def sorterNames(self):
        return self._sorter_names

    def getStudySortingResult(self, study_name, sorter_name):
        code0 = study_name+'----'+sorter_name
        sr = self._study_sorting_results_by_code.get(code0, None)
        return sr

    def getAccuracyCount(self, study_name, sorter_name, accuracy_thresh):
        sr = self.getStudySortingResult(study_name=study_name, sorter_name=sorter_name)
        if sr is None:
            return None
        n1s = sr['num_false_positives']
        n2s = sr['num_matches']
        n3s = sr['num_false_negatives']
        snrs = sr['true_unit_snrs']
        accuracies = []
        for i in range(len(n1s)):
            tot0 = n1s[i] + n2s[i] + n3s[i]
            if tot0 == 0:
                acc0 = 0
            else:
                acc0 = n2s[i] / tot0
            accuracies.append(acc0)
        accuracies = np.array(accuracies)
        snrs = np.array(snrs)
        count0 = np.count_nonzero((accuracies>=accuracy_thresh))
        return count0
        

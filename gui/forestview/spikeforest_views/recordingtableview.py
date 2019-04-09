import vdomr as vd
import time
import sys
import mtlogging
import numpy as np
import json
from .tablewidget import TableWidget

class RecordingTableView(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        self._recording_table_widget = RecordingTableWidget(context=context)
    def setSize(self, size):
        self._size=size
        if self._recording_table_widget:
            self._recording_table_widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Recording table'
    def render(self):
        return vd.div(
            self._recording_table_widget
        )

# class RecordingTableWidget(vd.Component):
#     def __init__(self, *, context):
#         vd.Component.__init__(self)
#         self._context = context
#         self._size = (100,100)
#     def setSize(self, size):
#         self._size = size
#         self.refresh()
#     def render(self):
#         return vd.pre(json.dumps(self._context.recordingNames(), indent=4))

class RecordingTableWidget(vd.Component):
    def __init__(self, *, context):
        vd.Component.__init__(self)
        self._size = (100,100)
        self._context = context
        self._update_table()
        self._context.onCurrentRecordingChanged(self._on_context_selection_changed)
    def setSize(self, size):
        self._size = size
        self._update_table()
    def _update_table(self):
        self._recording_ids = self._context.recordingIds()
        recobjs = [self._context.recordingObject(recid) for recid in self._recording_ids]
        records = [
            dict(
                study_name=obj['study'],
                recording_name=obj['name'],
                duration_sec=_get_computed_info(obj, 'duration_sec'),
                samplerate=_get_computed_info(obj, 'samplerate'),
                num_channels=_get_computed_info(obj, 'num_channels')
            )
            for obj in recobjs
        ]
        
        self._table_widget = TableWidget(
            columns = [
                dict(label='Study', name='study_name'),
                dict(label='Recording', name='recording_name'),
                dict(label='Duration (sec)', name='duration_sec'),
                dict(label='Sampling freq. (Hz)', name='samplerate'),
                dict(label='Num. channels', name='num_channels'),
            ],
            records = records,
            height=self._size[1]
        )
        self._table_widget.onSelectionChanged(self._on_widget_selection_changed)
        self._on_context_selection_changed()
        self.refresh()
    def _on_widget_selection_changed(self):
        current_row_index = self._table_widget.currentRowIndex()
        if current_row_index is not None:
            self._context.setCurrentRecordingId(self._recording_ids[current_row_index])
        else:
            self._context.setCurrentRecordingId(None)
    def _on_context_selection_changed(self):
        recid = self._context.currentRecordingId()
        if recid is not None:
            try:
                index0 = self._recording_ids.index(recid)
            except:
                index0 = None
        else:
            index0 = None
        self._table_widget.setCurrentRowIndex(index0)

    def render(self):
        return self._table_widget

def _get_computed_info(recobj, name):
    summary = recobj.get('summary', dict())
    computed_info = summary.get('computed_info', dict())
    return computed_info.get(name, None)
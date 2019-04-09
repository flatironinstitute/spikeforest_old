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
    def setSize(self, size):
        self._size = size
        self._update_table()
    def _update_table(self):
        recording_names = self._context.recordingNames()
        recording_infos = [self._context.recordingInfo(rname) for rname in recording_names]
        records = [
            dict(
                recording_name=rname,
                duration = recording_infos[ii].get('duration', '[unknown]'),
                num_channels = recording_infos[ii].get('num_channels', '[unknown]')
            )
            for ii, rname in enumerate(recording_names)
        ]
        self._table_widget = TableWidget(
            columns = [
                dict(label='Recording', name='recording_name'),
                dict(label='Duration', name='duration'),
                dict(label='Num. channels', name='num_channels')
            ],
            records = records,
            height=self._size[1]
        )
        self.refresh()
    def render(self):
        return self._table_widget

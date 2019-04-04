import vdomr as vd
import time
import sys
import mtlogging
import numpy as np
import json

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

class RecordingTableWidget(vd.Component):
    def __init__(self, *, context):
        vd.Component.__init__(self)
        self._context = context
        self._size = (100,100)
    def setSize(self, size):
        self._size = size
        self.refresh()
    def render(self):
        return vd.pre(json.dumps(self._context.recordingNames(), indent=4))


import vdomr as vd
import time
import sys
import mtlogging
from mountaintools import client as mt
from .tablewidget import TableWidget
import json

class SortingResultDetailView(vd.Component):
    def __init__(self, context, opts=None):
        vd.Component.__init__(self)
        self._sr_context = context
        self._size=(100, 100)
        self._widget = SortingResultDetailWidget(
            context=self._sr_context
        )
        self._widget.setSize(self._size)
    def setSize(self, size):
        self._size=size
        if self._widget:
            self._widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Sorting result detail'
    def render(self):
        return self._widget

class SortingResultDetailWidget(vd.Component):
    def __init__(self, *, context):
        vd.Component.__init__(self)
        self._sr_context = context
        self._size = (100,100)
    def setSize(self, size):
        self._size = size
    def render(self):
        sr = self._sr_context.sortingResultObject()
        return vd.components.ScrollArea(vd.pre(json.dumps(sr, indent=4)), height=self._size[1])


import vdomr as vd
import time
import sys
import mtlogging
import numpy as np
from copy import deepcopy
from spikeforest import EfficientAccessRecordingExtractor
import spikeforestwidgets as SFW

class FeatureSpaceView(vd.Component):
    def __init__(self, *, context, opts=None, prepare_result=None):
        vd.Component.__init__(self)
        self._sorting_context = context
        self._recording_context = context.recordingContext()
        self._size = (100, 100)
        self._rx = EfficientAccessRecordingExtractor(path=prepare_result['earx_path'])
        unit_ids = self._sorting_context.selectedUnitIds()
        self._widget = SFW.FeatureSpaceWidgetPlotly(recording=self._rx, sorting=self._sorting_context.sortingExtractor(), unit_ids=unit_ids)
        self._widget.setSize(self._size)
        self.refresh()
    @staticmethod
    def prepareView(context, opts):
        sorting_context = context
        recording_context = context.recordingContext()
        sorting_context.initialize()
        earx = EfficientAccessRecordingExtractor(recording=recording_context.recordingExtractor())
        return dict(
            earx_path = earx.path()
        )
    def setSize(self, size):
        if self._size != size:
            self._size=size
        if self._widget:
            self._widget.setSize(size)

    def size(self):
        return self._size
    def tabLabel(self):
        return 'Feature space'
    def render(self):
        return self._widget
import vdomr as vd
import spikeforestwidgets as SFW
from spikeforest import EfficientAccessRecordingExtractor
import spikeextractors as se
import time
import multiprocessing
import sys
from .stdoutsender import StdoutSender
import mtlogging
class TimeseriesView(vd.Component):
    def __init__(self, *, context, opts, prepare_result):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        self._opts=opts
        
        earx = EfficientAccessRecordingExtractor(path=prepare_result['earx_file'])
        self._timeseries_widget = SFW.TimeseriesWidget(recording=earx)
        self._timeseries_widget.setSize(self._size)


    # this will be done in a worker thread
    @staticmethod
    def prepareView(context, opts):
        print('***** Initializing context...')
        context.initialize()

        rx = context.recordingExtractor()

        print('***** Preparing efficient access recording extractor...')
        earx = EfficientAccessRecordingExtractor(recording=rx)
        
        print('***** Precomputing multiscale recordings...')
        SFW.precomputeMultiscaleRecordings(recording=earx)
        return dict(
            earx_file=earx.path()
        )

    def setSize(self, size):
        self._size=size
        if self._timeseries_widget:
            self._timeseries_widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Timeseries'
    def title(self):
        return 'Timeseries for {}'.format(self._context.recordingLabel())
    def render(self):
        return vd.div(
            self._timeseries_widget
        )

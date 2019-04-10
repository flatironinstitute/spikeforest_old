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
    def __init__(self, *, context, opts=None, prepare_result):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        
        earx = EfficientAccessRecordingExtractor(path=prepare_result['earx_file'])
        self._timeseries_widget = SFW.TimeseriesWidget(recording=earx)
        self._timeseries_widget.setSize(self._size)


    # this will be done in a worker thread
    @staticmethod
    def prepareView(context, opts=None):
        print('***** Initializing context...')
        context.initialize()

        print('***** Preparing efficient access recording extractor...')
        earx = EfficientAccessRecordingExtractor(recording=context.recordingExtractor())
        
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
    def render(self):
        return vd.div(
            self._timeseries_widget
        )

# Initialization in a worker thread
mtlogging.log(root=True)
def _initialize(context, connection_to_parent):
    context.initialize()
    with StdoutSender(connection=connection_to_parent):
        print('***** Preparing efficient access recording extractor...')
        earx = EfficientAccessRecordingExtractor(recording=context.recordingExtractor())
        
        print('***** Precomputing multiscale recordings...')
        SFW.precomputeMultiscaleRecordings(recording=earx)
    connection_to_parent.send(dict(
        name='result',
        result=dict(
            earx_file=earx.path()
        )
    )) 
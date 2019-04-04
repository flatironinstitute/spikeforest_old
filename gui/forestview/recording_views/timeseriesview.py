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
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        self._timeseries_widget = None


        self._connection_to_init, connection_to_parent = multiprocessing.Pipe()
        self._init_process = multiprocessing.Process(target=_initialize, args=(context, connection_to_parent))
        self._init_process.start()

        self._init_log_text = ''
        vd.set_timeout(self._check_init, 0.5)
    def _on_init_completed(self, init):
        earx = EfficientAccessRecordingExtractor(path=init['earx_file'])
        self._timeseries_widget = SFW.TimeseriesWidget(recording=earx)
        self._timeseries_widget.setSize(self._size)
        self.refresh()
    def setSize(self, size):
        self._size=size
        if self._timeseries_widget:
            self._timeseries_widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Timeseries'
    def render(self):
        if self._timeseries_widget:
            return vd.div(
                self._timeseries_widget
            )
        else:
            return vd.div(
                vd.h3('Initializing...'),
                vd.pre(self._init_log_text)
            )
    def _check_init(self):
        if not self._timeseries_widget:
            if self._connection_to_init.poll():
                msg = self._connection_to_init.recv()
                if msg['name'] == 'log':
                    self._init_log_text = self._init_log_text + msg['text']
                    self.refresh()
                elif msg['name'] == 'result':
                    self._on_init_completed(msg['result'])
                    return
            vd.set_timeout(self._check_init, 1)

# Initialization in a worker thread
mtlogging.log(root=True)
def _initialize(context, connection_to_parent):
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
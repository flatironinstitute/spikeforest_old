import vdomr as vd
import time
import multiprocessing
import sys
from .stdoutsender import StdoutSender
import mtlogging
import numpy as np

class TestPlotlyView(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        self._test_plotly_widget = None

        self._connection_to_init, connection_to_parent = multiprocessing.Pipe()
        self._init_process = multiprocessing.Process(target=_initialize, args=(context, connection_to_parent))
        self._init_process.start()

        self._init_log_text = ''
        vd.set_timeout(self._check_init, 0.5)
    def _on_init_completed(self, init):
        self._test_plotly_widget = TestPlotlyWidget()
        self._test_plotly_widget.setSize(self._size)
        self.refresh()
    def setSize(self, size):
        self._size=size
        if self._test_plotly_widget:
            self._test_plotly_widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Test plotly'
    def render(self):
        if self._test_plotly_widget:
            return vd.div(
                self._test_plotly_widget
            )
        else:
            return vd.div(
                vd.h3('Initializing...'),
                vd.pre(self._init_log_text)
            )
    def _check_init(self):
        if not self._test_plotly_widget:
            if self._connection_to_init.poll():
                msg = self._connection_to_init.recv()
                if msg['name'] == 'log':
                    self._init_log_text = self._init_log_text + msg['text']
                    self.refresh()
                elif msg['name'] == 'result':
                    self._on_init_completed(msg['result'])
                    return
            vd.set_timeout(self._check_init, 1)

class TestPlotlyWidget(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._size = (100,100)
        self._plot=None
        self._update_plot()
    def setSize(self, size):
        self._size = size
        self._update_plot()
    def _update_plot(self):
        xx = np.linspace(0,1,10)
        yy = np.cos((10*xx)**2)
        self._plot = vd.components.PlotlyPlot(
            data = dict(x=xx, y=yy),
            layout=dict(margin=dict(t=5)),
            config=dict(),
            size=self._size
        )
        self.refresh()
    def render(self):
        if not self._plot:
            return vd.div('no plot.')
        return self._plot

# Initialization in a worker thread
mtlogging.log(root=True)
def _initialize(context, connection_to_parent):
    with StdoutSender(connection=connection_to_parent):
        pass
    connection_to_parent.send(dict(
        name='result',
        result=dict()
    )) 
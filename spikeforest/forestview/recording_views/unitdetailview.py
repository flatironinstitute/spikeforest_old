import vdomr as vd
import time
import multiprocessing
import sys
from .stdoutsender import StdoutSender
import mtlogging
import numpy as np
from spikeforest import EfficientAccessRecordingExtractor
import json
import mlprocessors as mlpr
import traceback
from mountaintools import client as mt
import pickle

class UnitDetailView(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._unit_id = context.currentUnitId()
        self._size=(100, 100)
        self._unit_detail_widget = None

        if self._unit_id is None:
            return

        self._connection_to_init, connection_to_parent = multiprocessing.Pipe()
        self._init_process = multiprocessing.Process(target=_initialize, args=(context, self._unit_id, connection_to_parent))
        self._init_process.start()

        self._init_log_text = ''
        vd.set_timeout(self._check_init, 0.5)
    def _on_init_completed(self, result):
        self._unit_detail_widget = UnitDetailWidget(context=self._context, unit_id=self._unit_id, init_result=result)
        self._unit_detail_widget.setSize(self._size)
        self.refresh()
    def setSize(self, size):
        self._size=size
        if self._unit_detail_widget:
            self._unit_detail_widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Unit {}'.format(self._unit_id)
    def render(self):
        if self._unit_id is None:
            return vd.div(vd.h3('No current unit selected.'))
        if self._unit_detail_widget:
            return vd.div(
                self._unit_detail_widget
            )
        else:
            return vd.div(
                vd.h3('Initializing......'),
                vd.pre(self._init_log_text),
                style=dict(overflow='auto')
            )
    def _check_init(self):
        if not self._unit_detail_widget:
            if self._connection_to_init.poll():
                msg = self._connection_to_init.recv()
                if msg['name'] == 'log':
                    self._init_log_text = self._init_log_text + msg['text']
                    self.refresh()
                elif msg['name'] == 'result':
                    self._on_init_completed(msg['result'])
                    return
            vd.set_timeout(self._check_init, 1)

class UnitDetailWidget(vd.Component):
    def __init__(self, *, context, unit_id, init_result):
        vd.Component.__init__(self)
        self._context = context
        self._unit_id = unit_id
        self._init_result = init_result
        self._size = (100,100)
    def setSize(self, size):
        self._size = size
        self.refresh()
    def render(self):
        result0 = self._init_result
        snippets = result0['snippets']
        template = result0['template']
        peak_chan_index=np.argmax(np.max(np.abs(template),axis=1),axis=0)
        peak_chan=self._context.recordingExtractor().getChannelIds()[peak_chan_index]
        return vd.div(
            vd.pre(
                'Unit {} has {} events. Peak is on channel {}.'.format(self._unit_id, result0['num_events'], peak_chan)
            ),
            SnippetsPlot(snippets=snippets, channel_index=peak_chan_index, size=(self._size[0],self._size[1]-50))
        )

class SnippetsPlot(vd.Component):
    def __init__(self, *, snippets, channel_index, size):
        vd.Component.__init__(self)
        data=[]
        for snippet in snippets:
            # M = snippet.shape[0]
            T = snippet.shape[1]
            data.append(dict(
                x=np.arange(0,T),
                y=snippet[channel_index,:]
            ))
        self._plot = vd.components.PlotlyPlot(
            data=data,
            layout=dict(
                showlegend=False
            ),
            config=dict(),
            size=size
        )
    def render(self):
        return vd.div(
            self._plot
        )


# Initialization in a worker thread
mtlogging.log(root=True)
def _initialize(context, unit_id, connection_to_parent):
    with StdoutSender(connection=connection_to_parent):
        try:
            print('***** Preparing efficient access recording extractor...')
            earx = EfficientAccessRecordingExtractor(recording=context.recordingExtractor())
            print('***** Computing unit detail...')
            path0 = mt.realizeFile(path=ComputeUnitDetail.execute(recording=earx, sorting=context.trueSortingExtractor(), unit_id=unit_id, output=True).outputs['output'])
            with open(path0, 'rb') as f:
                result0 = pickle.load(f)
            print('*****')
        except:
            traceback.print_exc()
            raise
    connection_to_parent.send(dict(
        name='result',
        result=result0
    )) 

class ComputeUnitDetail(mlpr.Processor):
    NAME = 'ComputeUnitsDetail'
    VERSION = '0.1.5'
    recording = mlpr.Input()
    sorting = mlpr.Input()
    unit_id = mlpr.IntegerParameter()
    output = mlpr.Output()

    def run(self):
        event_times = self.sorting.getUnitSpikeTrain(unit_id=self.unit_id) # pylint: disable=no-member
        snippets = self.recording.getSnippets(reference_frames=event_times, snippet_len=100) # pylint: disable=no-member
        template = np.median(np.stack(snippets), axis=0)
        result0 = dict(
            unit_id=self.unit_id,
            num_events=len(event_times),
            event_times=event_times,
            snippets=snippets,
            template=template
        )
        with open(self.output, 'wb') as f:
            pickle.dump(result0, f)
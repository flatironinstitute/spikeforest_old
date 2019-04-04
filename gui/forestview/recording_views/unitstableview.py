import vdomr as vd
import time
import multiprocessing
import sys
from .stdoutsender import StdoutSender
import mtlogging
import numpy as np
import spikeforest_analysis as sa
from spikeforest import EfficientAccessRecordingExtractor
import json
import mlprocessors as mlpr
import traceback
from mountaintools import client as mt

class UnitsTableView(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        self._unit_table_widget = None

        self._connection_to_init, connection_to_parent = multiprocessing.Pipe()
        self._init_process = multiprocessing.Process(target=_initialize, args=(context, connection_to_parent))
        self._init_process.start()

        self._init_log_text = ''
        vd.set_timeout(self._check_init, 0.5)
    def _on_init_completed(self, result):
        self._unit_table_widget = UnitTableWidget(context=self._context, units_info=result)
        self._unit_table_widget.setSize(self._size)
        self.refresh()
    def setSize(self, size):
        self._size=size
        if self._unit_table_widget:
            self._unit_table_widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Units table'
    def render(self):
        if self._unit_table_widget:
            return vd.div(
                self._unit_table_widget
            )
        else:
            return vd.div(
                vd.h3('Initializing......'),
                vd.pre(self._init_log_text),
                style=dict(overflow='auto')
            )
    def _check_init(self):
        if not self._unit_table_widget:
            if self._connection_to_init.poll():
                msg = self._connection_to_init.recv()
                if msg['name'] == 'log':
                    self._init_log_text = self._init_log_text + msg['text']
                    self.refresh()
                elif msg['name'] == 'result':
                    self._on_init_completed(msg['result'])
                    return
            vd.set_timeout(self._check_init, 1)

class UnitTableWidget(vd.Component):
    def __init__(self, *, context, units_info):
        vd.Component.__init__(self)
        self._size = (100,100)
        self._units_info = units_info
    def setSize(self, size):
        self._size = size
        self.refresh()
    def render(self):
        rows = []
        rows.append(vd.tr(
            vd.th('Unit ID'),
            vd.th('SNR'),
            vd.th('Peak channel'),
            vd.th('Num. events'),
            vd.th('Firing rate')
        ))
        if self._units_info:
            for unit in self._units_info:
                rows.append(vd.tr(
                    vd.td(str(unit['unit_id'])),
                    vd.td(str(unit['snr'])),
                    vd.td(str(unit['peak_channel'])),
                    vd.td(str(unit['num_events'])),
                    vd.td(str(unit['firing_rate']))
                ))
        else:
            print('WARNING: units info not found.')
        table = vd.table(rows, class_='table')
        return vd.div(ScrollArea(vd.div(table), height=self._size[1]))

class ScrollArea(vd.Component):
    def __init__(self, child, *, height):
        vd.Component.__init__(self)
        self._child = child
        self._height = height

    def render(self):
        return vd.div(self._child, style=dict(overflow='auto', height='{}px'.format(self._height)))

# Initialization in a worker thread
mtlogging.log(root=True)
def _initialize(context, connection_to_parent):
    with StdoutSender(connection=connection_to_parent):
        try:
            print('***** Preparing efficient access recording extractor...')
            earx = EfficientAccessRecordingExtractor(recording=context.recordingExtractor())
            print('***** computing units info...')
            info0 = mt.loadObject(path=ComputeUnitsInfo.execute(recording=earx, sorting=context.sortingExtractor(), json_out=True).outputs['json_out'])
            print('*****')
        except:
            traceback.print_exc()
            raise
    connection_to_parent.send(dict(
        name='result',
        result=info0
    )) 

class ComputeUnitsInfo(mlpr.Processor):
    NAME = 'ComputeUnitsInfo'
    VERSION = '0.1.3'
    recording = mlpr.Input()
    sorting = mlpr.Input()
    json_out = mlpr.Output()

    def run(self):
        info0 = sa.compute_units_info(recording=self.recording, sorting=self.sorting)
        with open(self.json_out, 'w') as f:
            json.dump(info0, f)
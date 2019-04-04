import vdomr as vd
import time
import multiprocessing
import sys
from .stdoutsender import StdoutSender
import mtlogging
import numpy as np
import spikeforest_analysis as sa
from spikeforest import EfficientAccessRecordingExtractor
import spikeforestwidgets as SFW
import json
from matplotlib import pyplot as plt
import mlprocessors as mlpr

class TemplatesView(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._size = (100, 100)
        self._templates_widget = None

        self._connection_to_init, connection_to_parent = multiprocessing.Pipe()
        self._init_process = multiprocessing.Process(target=_initialize, args=(context, connection_to_parent))
        self._init_process.start()

        self._init_log_text = ''
        vd.set_timeout(self._check_init, 0.5)
    def _on_init_completed(self, units):
        self._templates_widget = TemplatesWidget(units=units)
        #self._templates_widget.setSize(self._size)
        self.refresh()
    def setSize(self, size):
        if self._size != size:
            self._size=size
        #if self._templates_widget:
        #    self._templates_widget.setSize(size)

    def size(self):
        return self._size
    def tabLabel(self):
        return 'Unit table'
    def render(self):
        if self._templates_widget:
            return vd.div(
                self._templates_widget
            )
        else:
            return vd.div(
                vd.h3('Initializing...'),
                vd.pre(self._init_log_text)
            )
    def _check_init(self):
        if not self._templates_widget:
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
        sorting = context.sortingExtractor()
        unit_ids = sorting.getUnitIds()
        print('***** Computing unit templates...')
        #templates = compute_unit_templates(recording=earx, sorting=sorting, unit_ids=unit_ids)
        templates = ComputeUnitTemplates.execute(recording=earx, sorting=sorting, unit_ids=unit_ids, templates_out=True).outputs['templates_out']
        print('*****')
    connection_to_parent.send(dict(
        name='result',
        result=[
            dict(
                template=templates[:,:,i],
                unit_id=unit_id
            )
            for i, unit_id in enumerate(unit_ids)
        ]
    ))

def get_random_spike_waveforms(*,recording,sorting,unit,snippet_len,max_num,channels=None):
    st=sorting.getUnitSpikeTrain(unit_id=unit)
    num_events=len(st)
    if num_events>max_num:
        event_indices=np.random.choice(range(num_events),size=max_num,replace=False)
    else:
        event_indices=range(num_events)

    spikes=recording.getSnippets(reference_frames=st[event_indices].astype(int),snippet_len=snippet_len,channel_ids=channels)
    if len(spikes)>0:
      spikes=np.dstack(tuple(spikes))
    else:
      spikes=np.zeros((recording.getNumChannels(),snippet_len,0))
    return spikes

def compute_unit_templates(*,recording,sorting,unit_ids,snippet_len=50,max_num=100,channels=None):
    M = len(recording.getChannelIds())
    T = snippet_len
    K = len(unit_ids)
    ret = np.zeros((M,T,K))
    for i, unit in enumerate(unit_ids):
        print('Unit {} of {} (id={})'.format(i, len(unit_ids), unit))
        waveforms = get_random_spike_waveforms(recording=recording, sorting=sorting, unit=unit, snippet_len=snippet_len, max_num=max_num, channels=None)
        template = np.median(waveforms,axis=2)
        ret[:,:,i] = template
    
    return ret


class ComputeUnitTemplates(mlpr.Processor):
    NAME = 'ComputeUnitTemplates'
    VERSION = '0.1.4'
    recording = mlpr.Input()
    sorting = mlpr.Input()
    templates_out = mlpr.OutputArray()

    def run(self):
        templates = compute_unit_templates(recording=self.recording, sorting=self.sorting, unit_ids=self.sorting.getUnitIds())
        print('Saving templates...')
        np.save(self.templates_out, templates)
        

class TemplatesWidget(vd.Component):
  def __init__(self,*,units):
    vd.Component.__init__(self)
    y_scale_factor = _compute_initial_y_scale_factor(units)
    self._widgets=[
        TemplateWidget(
            template=unit['template'],
            unit_id=unit['unit_id'],
            y_scale_factor=y_scale_factor
        )
        for unit in units
    ]
    vd.devel.loadBootstrap()
  def setSelectedUnitIds(self,ids):
    ids=set(ids)
    for W in self._widgets:
        W.setSelected(W.unitId() in ids)
  def render(self):
    box_style=dict(float='left')
    boxes=[
        vd.div(W,style=box_style)
        for W in self._widgets
    ]
    div=vd.div(boxes)
    return div

def _compute_initial_y_scale_factor(units):
    templates_list = [unit['template'] for unit in units]
    all_templates = np.stack(templates_list)
    all_abs_vals = np.abs(all_templates.ravel())
    vv = np.percentile(all_abs_vals, 99)
    if vv>0:
        return 1/(2*vv)
    else:
        return 1
class TemplateWidget(vd.Component):
  def __init__(self,*,unit_id,template,y_scale_factor=None):
    vd.Component.__init__(self)
    self._plot=SFW.TemplateWidget(template=template)
    self._plot.setYScaleFactor(y_scale_factor)
    self._unit_id=unit_id
    self._selected=False
  def setSelected(self,val):
    if self._selected==val:
        return
    self._selected=val
    self.refresh()
  def unitId(self):
    return self._unit_id
  def render(self):
    style0={'border':'solid 1px black','margin':'5px'}
    style1={}
    if self._selected:
        style1['background-color']='yellow'
    return vd.div(
        vd.p('Unit {}'.format(self._unit_id),style={'text-align':'center'}),
        vd.div(self._plot,style=style0),
        style=style1
    )

class _TemplatePlot(vd.components.Pyplot):
  def __init__(self,*,template):
    vd.components.Pyplot.__init__(self)
    self._template=template
  def plot(self):
    #W=sw.UnitWaveformsWidget(recording=self._recording,sorting=self._sorting,unit_ids=[self._unit_id],width=5,height=5)
    #W.plot()
    _plot_template(
        template=self._template
    )

def _plot_template(*,template):
  M = template.shape[0]
  T = template.shape[1]
  tt = np.arange(T)
  for m in range(M):
    plt.plot(tt, template[m,:])


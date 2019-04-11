import vdomr as vd
import time
import multiprocessing
import sys
from .stdoutsender import StdoutSender
import mtlogging
import numpy as np
from copy import deepcopy
import spikeforest_analysis as sa
from spikeforest import EfficientAccessRecordingExtractor
import spikeforestwidgets as SFW
import json
from matplotlib import pyplot as plt
import mlprocessors as mlpr
import uuid

class TemplatesView(vd.Component):
    def __init__(self, *, context, opts=None, prepare_result):
        vd.Component.__init__(self)
        self._sorting_context = context
        self._recording_context = context.recordingContext()
        self._size = (100, 100)
        units = prepare_result['units']
        self._templates_widget = TemplatesWidget(units=units)
        self._update_selected()
        self._templates_widget.onSelectedUnitIdsChanged(lambda: self._sorting_context.setSelectedUnitIds(self._templates_widget.selectedUnitIds()))
        self._sorting_context.onSelectedUnitIdsChanged(lambda: self._templates_widget.setSelectedUnitIds(self._sorting_context.selectedUnitIds()))
        self._templates_widget.onCurrentUnitIdChanged(lambda: self._sorting_context.setCurrentUnitId(self._templates_widget.currentUnitId()))
        self._sorting_context.onCurrentUnitIdChanged(lambda: self._templates_widget.setCurrentUnitId(self._sorting_context.currentUnitId()))
        #self._templates_widget.setSize(self._size)
        self.refresh()
    @staticmethod
    def prepareView(context, opts):
        sorting_context = context
        recording_context = context.recordingContext()
        sorting_context.initialize()
        earx = EfficientAccessRecordingExtractor(recording=recording_context.recordingExtractor())
        sorting = sorting_context.sortingExtractor()
        unit_ids = sorting.getUnitIds()
        print('***** Computing unit templates...')
        #templates = compute_unit_templates(recording=earx, sorting=sorting, unit_ids=unit_ids)
        templates = ComputeUnitTemplates.execute(recording=earx, sorting=sorting, unit_ids=unit_ids, templates_out=True).outputs['templates_out']
        print('*****')
        return dict(units=[
            dict(
                template=templates[:,:,i],
                unit_id=unit_id
            )
            for i, unit_id in enumerate(unit_ids)
        ])
    def setSize(self, size):
        if self._size != size:
            self._size=size
        #if self._templates_widget:
        #    self._templates_widget.setSize(size)

    def size(self):
        return self._size
    def tabLabel(self):
        return 'Templates'
    def render(self):
        return self._templates_widget

    def _update_selected(self):
        self._templates_widget.setSelectedUnitIds(self._sorting_context.selectedUnitIds())
        self._templates_widget.setCurrentUnitId(self._sorting_context.currentUnitId())

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
        templates = compute_unit_templates(recording=self.recording, sorting=self.sorting, unit_ids=self.sorting.getUnitIds()) # pylint: disable=no-member
        print('Saving templates...')
        np.save(self.templates_out, templates)
        

class TemplatesWidget(vd.Component):
  def __init__(self,*,units):
    vd.Component.__init__(self)
    y_scale_factor = _compute_initial_y_scale_factor(units)
    self._current_unit_id = None
    self._selected_unit_ids = []
    self._selected_unit_ids_changed_handlers = []
    self._current_unit_id_changed_handlers = []
    self._widgets=[
        TemplateWidget(
            template=unit['template'],
            unit_id=unit['unit_id'],
            y_scale_factor=y_scale_factor,
            size=(150,300)
        )
        for unit in units
    ]
    self._uuid=str(uuid.uuid4())
    vd.register_callback(self._uuid+'_box_clicked', self._handle_box_clicked)
    vd.devel.loadBootstrap()
  def setSelectedUnitIds(self,ids):
    if ids is None:
        ids=[]
    ids = sorted([int(id) for id in ids])
    if ids == self._selected_unit_ids:
        return
    self._selected_unit_ids = ids
    ids_set=set(ids)
    for W in self._widgets:
        W.setSelected(W.unitId() in ids_set)
    for handler in self._selected_unit_ids_changed_handlers:
        handler()

  def selectedUnitIds(self):
      return deepcopy(self._selected_unit_ids)

  def onSelectedUnitIdsChanged(self, handler):
      self._selected_unit_ids_changed_handlers.append(handler)

  def setCurrentUnitId(self,id):
    if id == self._current_unit_id:
        return
    self._current_unit_id = id
    for W in self._widgets:
        W.setCurrent(W.unitId() == id)
    for handler in self._current_unit_id_changed_handlers:
        handler()

  def currentUnitId(self):
      return self._current_unit_id

  def onCurrentUnitIdChanged(self, handler):
      self._current_unit_id_changed_handlers.append(handler)
    
  def _handle_box_clicked(self, *, index, ctrlKey):
      W = self._widgets[int(index)]
      if ctrlKey:
          a = self.selectedUnitIds()
          if W.unitId() in a:
              a.remove(W.unitId())
          else:
              a.append(W.unitId())
          self.setSelectedUnitIds(a)
      else:
        self.setSelectedUnitIds([W.unitId()])
        self.setCurrentUnitId(W.unitId())

  def render(self):
    box_style=dict(float='left')
    boxes=[
        vd.div(W,id=self._uuid+'-{}'.format(i),style=box_style)
        for i,W in enumerate(self._widgets)
    ]
    div=vd.div(
        boxes,
        style=dict(overflow='auto',height='100%')
    )
    return div

  def postRenderScript(self):
      js="""
      for (let i=0; i<{num_widgets}; i++) {
          (function(index) {
            let elmt = document.getElementById('{uuid}-'+index);
            if (elmt) {
                elmt.onclick=function(evt) {
                    window.vdomr_invokeFunction('{box_clicked_callback_id}', [], {index:index, ctrlKey:evt.ctrlKey});
                }
            }
          })(i);
      }
      """
      js=js.replace('{num_widgets}', str(len(self._widgets)))
      js=js.replace('{uuid}', self._uuid)
      js=js.replace('{box_clicked_callback_id}', self._uuid+'_box_clicked')
      return js

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
  def __init__(self,*,unit_id,template,y_scale_factor=None,size=(200,200)):
    vd.Component.__init__(self)
    self._unit_id=unit_id
    self._selected=False
    self._current=False
    self._size=size
    self._size_plot=(size[0]-20, size[1]-40)
    self._plot=SFW.TemplateWidget(template=template,size=self._size_plot)
    self._plot.setYScaleFactor(y_scale_factor)
  def setSelected(self,val):
    if self._selected==val:
        return
    self._selected=val
    self.refresh()
  def setCurrent(self,val):
    if self._current==val:
        return
    self._current=val
    self.refresh()
  def unitId(self):
    return self._unit_id
  def render(self):
    style_plot={'position':'relative', 'border':'solid 1px black', 'background-color':'white', 'left':'10px', 'bottom':'10px', 'width':'{}px'.format(self._size_plot[0]), 'height':'{}px'.format(self._size_plot[1])}
    style1={'width':'{}px'.format(self._size[0]), 'height':'{}px'.format(self._size[1])}
    if self._selected:
        style1['background-color']='rgb(240,240,200)'
        style1['border']='solid 1px gray'
        if self._current:
            style1['background-color']='rgb(220,220,180)'
    if self._current:
        style1['border']='solid 2px rgb(150,50,50)'
    return vd.div(
        vd.p('Unit {}'.format(self._unit_id),style={'text-align':'center'}),
        vd.div(self._plot,style=style_plot,size=()),
        style=style1
    )



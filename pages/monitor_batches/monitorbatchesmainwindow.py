import os
import vdomr as vd
import spikeforest as sf
from kbucket import client as kb

class MonitorBatchesMainWindow(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
    self._groups=kb.loadObject(key=dict(name='spikeforest_batch_group_names'))
    self._SEL_group=vd.components.SelectBox(options=self._groups['batch_group_names'])
    self._SEL_group.onChange(self._on_group_changed)
    self._BMW=sf.BatchMonitorWidget([],height=600)
    self._on_group_changed(value=self._SEL_group.value())
  def _on_group_changed(self,value):
    group_name=self._SEL_group.value()
    a=kb.loadObject(key=dict(name='spikeforest_batch_group',group_name=group_name))
    self._BMW.setBatchNames(a['batch_names'])
  def render(self):
    return vd.div(
      vd.h3('Select batch group----:'),
      self._SEL_group,
      self._BMW
    )
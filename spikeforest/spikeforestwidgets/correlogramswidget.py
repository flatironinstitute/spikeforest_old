import numpy as np
from matplotlib import pyplot as plt
import vdomr as vd

class CorrelogramsWidget(vd.Component):
  def __init__(self,*,sorting,samplerate):
    vd.Component.__init__(self)
    self._widgets=[
        CorrelogramWidget(
            sorting=sorting,
            samplerate=samplerate,
            unit1_id=id,
            unit2_id=id
        )
        for id in sorting.getUnitIds()
    ]
    vd.devel.loadBootstrap()
  def setSelectedUnitIds(self,ids):
    ids=set(ids)
    for W in self._widgets:
        W.setSelected(W.unit1Id() in ids)
  def render(self):
    box_style=dict(float='left')
    boxes=[
        vd.div(W,style=box_style)
        for W in self._widgets
    ]
    div=vd.div(boxes)
    return div

class CorrelogramWidget(vd.Component):
  def __init__(self,*,sorting,samplerate,unit1_id,unit2_id):
    vd.Component.__init__(self)
    self._plot=_CorrelogramPlot(
        sorting=sorting,
        samplerate=samplerate,
        unit1_id=unit1_id,
        unit2_id=unit2_id
    )
    self._plot_div=vd.components.LazyDiv(self._plot)
    self._unit1_id=unit1_id
    self._unit2_id=unit2_id
    self._selected=False
  def setSelected(self,val):
    if self._selected==val:
        return
    self._selected=val
    self.refresh()
  def unit1Id(self):
    return self._unit1_id
  def unit2Id(self):
    return self._unit1_id
  def render(self):
    style0={'border':'solid 1px black','margin':'5px'}
    style1={}
    if self._selected:
        style1['background-color']='yellow'
    return vd.div(
        vd.p('Unit {}'.format(self._unit_id),style={'text-align':'center'}),
        vd.div(self._plot_div,style=style0),
        style=style1
    )
  def render(self):
    style0={'border':'solid 1px black','margin':'5px'}
    style1={}
    if self._selected:
        style1['background-color']='yellow'
    if self._unit1_id==self._unit2_id:
        title0='Unit {}'.format(self._unit1_id)
    else:
        title0='{} / {}'.format(self._unit1_id,self._unit2_id)
    return vd.div(
        vd.p(title0,style={'text-align':'center'}),
        vd.div(self._plot_div,style=style0),
        style=style1
    )

import time
from spikeforest import spikewidgets as sw
class _CorrelogramPlot(vd.components.Pyplot):
  def __init__(self,*,sorting,samplerate,unit1_id,unit2_id):
    vd.components.Pyplot.__init__(self)
    self._sorting=sorting
    self._samplerate=samplerate
    self._unit1_id=unit1_id
    self._unit2_id=unit2_id
  def plot(self):
    plot_correlogram(
        sorting=self._sorting,
        samplerate=self._samplerate,
        unit1_id=self._unit1_id,
        unit2_id=self._unit2_id
    )

def _plot_correlogram_helper(*, bin_counts, bin_edges, title=''):
    wid = (bin_edges[1] - bin_edges[0]) * 1000
    plt.bar(x=bin_edges[0:-1] * 1000, height=bin_counts, width=wid, color='gray', align='edge')
    plt.xlabel('dt (msec)')
    plt.gca().get_yaxis().set_ticks([])
    plt.gca().get_xaxis().set_ticks([])
    plt.gca().get_yaxis().set_ticks([])
    if title:
        plt.title(title, color='gray')

def compute_autocorrelogram(times, *, max_dt_tp, bin_size_tp, max_samples=None):
    num_bins_left = int(max_dt_tp / bin_size_tp)  # number of bins to the left of the origin
    L = len(times)  # number of events
    times2 = np.sort(times)  # the sorted times
    step = 1  # This is the index step between an event and the next one to compare
    candidate_inds = np.arange(L)  # These are the events we are going to consider
    if max_samples is not None:
        if len(candidate_inds) > max_samples:
            candidate_inds = np.random.choice(candidate_inds, size=max_samples, replace=False)
    vals_list = []  # A list of all offsets we have accumulated
    while True:
        candidate_inds = candidate_inds[
            candidate_inds + step < L]  # we only consider events that are within workable range
        candidate_inds = candidate_inds[times2[candidate_inds + step] - times2[
            candidate_inds] <= max_dt_tp]  # we only consider event-pairs that are within max_dt_tp apart
        if len(candidate_inds) > 0:  # if we have some events to consider
            vals = times2[candidate_inds + step] - times2[candidate_inds]
            vals_list.append(vals)  # add to the autocorrelogram
            vals_list.append(-vals)  # keep it symmetric
        else:
            break  # no more to consider
        step += 1
    if len(vals_list) > 0:  # concatenate all the values
        all_vals = np.concatenate(vals_list)
    else:
        all_vals = np.array([]);
    aa = np.arange(-num_bins_left, num_bins_left + 1) * bin_size_tp
    all_vals = np.sign(all_vals) * (np.abs(
        all_vals) - bin_size_tp * 0.00001)  # a trick to make the histogram symmetric due to differences in rounding for positive and negative, i suppose
    bin_counts, bin_edges = np.histogram(all_vals, bins=aa)
    return (bin_counts, bin_edges)
        
def plot_correlogram(*,sorting,samplerate,unit1_id,unit2_id,title=''):
    if unit1_id != unit2_id:
        raise Exception('This case not supported yet.')
    times = sorting.getUnitSpikeTrain(unit_id=unit1_id)
    max_dt_msec = 50
    bin_size_msec = 2
    max_dt_tp = max_dt_msec * samplerate / 1000
    bin_size_tp = bin_size_msec * samplerate / 1000
    (bin_counts, bin_edges) = compute_autocorrelogram(times, max_dt_tp=max_dt_tp, bin_size_tp=bin_size_tp)
    _plot_correlogram_helper(bin_counts=bin_counts,bin_edges=bin_edges,title=title)

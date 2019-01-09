import numpy as np
from matplotlib import pyplot as plt
import vdomr as vd

class UnitWaveformsWidget(vd.Component):
  def __init__(self,*,recording,sorting,max_num_spikes_per_unit=20):
    vd.Component.__init__(self)
    self._widgets=[
        UnitWaveformWidget(
            recording=recording,
            sorting=sorting,
            unit_id=id,
            max_num_spikes_per_unit=max_num_spikes_per_unit
        )
        for id in sorting.getUnitIds()
    ]
    vd.devel.loadBootstrap()
  def render(self):
    box_style=dict(float='left')
    boxes=[
        vd.div(W,style=box_style)
        for W in self._widgets
    ]
    div=vd.div(boxes)
    return vd.components.ScrollArea(div,height=500)

class UnitWaveformWidget(vd.Component):
  def __init__(self,*,recording,sorting,unit_id,max_num_spikes_per_unit=20):
    vd.Component.__init__(self)
    self._plot=_UnitWaveformPlot(
        recording=recording,
        sorting=sorting,
        unit_id=unit_id,
        max_num_spikes_per_unit=max_num_spikes_per_unit
    )
    self._unit_id=unit_id
  def render(self):
    style0={'border':'solid 1px black','margin':'5px'}
    plot=vd.components.LazyDiv(self._plot)
    return vd.div(
        vd.p('Unit {}'.format(self._unit_id),style={'text-align':'center'}),
        vd.div(plot,style=style0)
    )

import time
import spikewidgets as sw
class _UnitWaveformPlot(vd.components.Pyplot):
  def __init__(self,*,recording,sorting,unit_id,max_num_spikes_per_unit):
    vd.components.Pyplot.__init__(self)
    self._recording=recording
    self._sorting=sorting
    self._unit_id=unit_id
    self._max_num_spikes_per_unit=max_num_spikes_per_unit
  def plot(self):
    #W=sw.UnitWaveformsWidget(recording=self._recording,sorting=self._sorting,unit_ids=[self._unit_id],width=5,height=5)
    #W.plot()
    plot_unit_waveform(
        recording=self._recording,
        sorting=self._sorting,
        unit_id=self._unit_id,
        max_num_spikes_per_unit=self._max_num_spikes_per_unit
    )
    

  


def _compute_minimum_gap(x):
  a=np.sort(np.unique(x))
  if len(a)<=1:
    return 1
  return np.min(np.diff(a))

def _plot_spike_shapes(*, representative_waveforms=None, average_waveform=None, channel_locations=None,
                           ylim=None, max_representatives=None, color='blue', title=''):
    if average_waveform is None:
        if representative_waveforms is None:
            raise Exception('You must provide either average_waveform, representative waveforms, or both')
        average_waveform = np.mean(representative_waveforms, axis=2)
    M = average_waveform.shape[0]  # number of channels
    T = average_waveform.shape[1]  # number of timepoints
    
    if ylim is None:
        ylim = [average_waveform.min(), average_waveform.max()]
    yrange = ylim[1] - ylim[0]
    
    if channel_locations is None:
        channel_locations = np.zeros((M, 2))
        for m in range(M):
            channel_locations[m, :] = [0, -m]

    if channel_locations.shape[1]>2:
      channel_locations=channel_locations[:,-2:]
    
    xmin=np.min(channel_locations[:,0])
    xmax=np.max(channel_locations[:,0])
    ymin=np.min(channel_locations[:,1])
    ymax=np.max(channel_locations[:,1])
    xgap=_compute_minimum_gap(channel_locations[:,0])
    ygap=_compute_minimum_gap(channel_locations[:,1])

    xvals = np.linspace(-xgap*0.8 / 2, xgap*0.8 / 2, T)
    yscale=1/(yrange/2)*ygap/2*0.4
    
    ax = plt.axes([0,0,1,1], frameon=False)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.get_xaxis().set_ticks([])
    ax.get_yaxis().set_ticks([])
    
    if representative_waveforms is not None:
        if max_representatives is not None:
            W0 = representative_waveforms
            if W0.shape[2] > max_representatives:
                indices = np.random.choice(range(W0.shape[2]), size=max_representatives, replace=False)
                representative_waveforms = W0[:, :, indices]
        L = representative_waveforms.shape[2]
        XX = np.zeros((T, M, L))
        YY = np.zeros((T, M, L))
        for m in range(M):
            loc = channel_locations[m, -2:]
            for j in range(L):
                XX[:, m, j] = loc[0] + xvals
                YY[:, m, j] = loc[1] + (representative_waveforms[m, :, j] - representative_waveforms[m, 0, j])*yscale
        XX = XX.reshape(T, M * L)
        YY = YY.reshape(T, M * L)
        plt.plot(XX, YY, color=(0.5, 0.5, 0.5), alpha=0.4)

        XX = np.zeros((T, M))
        YY = np.zeros((T, M))
        for m in range(M):
            loc = channel_locations[m, -2:]
            XX[:, m] = loc[0] + xvals
            YY[:, m] = loc[1] + (average_waveform[m, :] - average_waveform[m, 0])*yscale
        plt.plot(XX, YY, color)
        
    plt.xlim(xmin-xgap/2,xmax+xgap/2)
    plt.ylim(ymin-ygap/2,ymax+ygap/2)
    
    #plt.gca().set_axis_off()
    if title:
        plt.title(title, color='gray')
        
def _get_random_spike_waveforms(*,recording, sorting, unit, max_num, channels, snippet_len):
    st = sorting.getUnitSpikeTrain(unit_id=unit)
    num_events = len(st)
    if num_events > max_num:
        event_indices = np.random.choice(range(num_events), size=max_num, replace=False)
    else:
        event_indices = range(num_events)

    spikes = recording.getSnippets(reference_frames=st[event_indices].astype(int), snippet_len=snippet_len,
                                  channel_ids=channels)
    if len(spikes)>0:
        spikes = np.dstack(tuple(spikes))
    else:
        spikes = np.zeros((recording.getNumChannels(), snippet_len, 0))
    return spikes

def plot_unit_waveform(*,recording,sorting,unit_id,max_num_spikes_per_unit,channel_ids=None,snippet_len=100,title=''):
  if not channel_ids:
    channel_ids=recording.getChannelIds()
  M = len(channel_ids)
  channel_locations = np.zeros((M, 2))
  for ii, ch in enumerate(channel_ids):
      loc = recording.getChannelProperty(ch, 'location')
      channel_locations[ii, :] = loc[-2:]
  
  spikes = _get_random_spike_waveforms(recording=recording,sorting=sorting,unit=unit_id, max_num=max_num_spikes_per_unit, channels=channel_ids, snippet_len=snippet_len)
  #if not title:
  #  title='Unit {}'.format(int(unit_id))
  
  _plot_spike_shapes(representative_waveforms=spikes,channel_locations=channel_locations, title=title)
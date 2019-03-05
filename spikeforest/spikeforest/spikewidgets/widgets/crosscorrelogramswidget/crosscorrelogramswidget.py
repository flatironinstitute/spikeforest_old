from matplotlib import pyplot as plt
import numpy as np

class CrossCorrelogramsWidget:
    def __init__(self, max_samples=None, auto=True, *, sorting, samplerate, unit_ids=None, _figure=None, _axs=None):
        self._SX = sorting
        self._unit_ids = unit_ids
        self._figure = _figure
        self._axs = _axs
        if self._figure is not None:
            self._axs = self._figure.axes
        elif self._axs is not None:
            self._axs = self._axs
        self._samplerate = samplerate
        self.auto = auto
        self.max_samples = max_samples
        self.max_dt_msec = 50
        self.bin_size_msec = 2
        self.max_dt_tp = self.max_dt_msec * self._samplerate / 1000
        self.bin_size_tp = self.bin_size_msec * self._samplerate / 1000

    def plot(self):
        if self.auto:
            self._do_plot()
        else:
            self._do_plot_matrix()

    def figure(self):
        return self._figure

    def _do_plot_matrix(self):
        units = self._unit_ids
        if units is None:
            units = self._SX.getUnitIds()
        nrows = ncols = len(units)
        f,axs = plt.subplots(nrows,ncols,figsize=(3 * ncols + 0.1, 3 * nrows + 0.1))
        self._figure = f
        for i1,unit1 in enumerate(units):
            times1 = self._SX.getUnitSpikeTrain(unit_id=unit1)
            for i2,unit2 in enumerate(units):
                times2 = self._SX.getUnitSpikeTrain(unit_id=unit2)
                if i1 == i2:
                    (bin_counts, bin_edges) = compute_crosscorrelogram(times1, max_dt_tp=self.max_dt_tp, bin_size_tp=self.bin_size_tp, max_samples=self.max_samples)
                else:
                    (bin_counts, bin_edges) = compute_crosscorrelogram(times1, times2, max_dt_tp=self.max_dt_tp, bin_size_tp=self.bin_size_tp, max_samples=self.max_samples)
                item = dict(
                        title="{} -> {}".format(unit1, unit2),
                        bin_counts=bin_counts,
                        bin_edges=bin_edges
                        )
                self._plot_correlogram(axs[i1,i2], **item)

    def _do_plot(self):
        units = self._unit_ids
        if units is None:
            units = self._SX.getUnitIds()
        list = []
        for unit in units:
            times = self._SX.getUnitSpikeTrain(unit_id=unit)
            (bin_counts, bin_edges) = compute_autocorrelogram(times, max_dt_tp=self.max_dt_tp, bin_size_tp=self.bin_size_tp)
            item = dict(
                    title=str(unit),
                    bin_counts=bin_counts,
                    bin_edges=bin_edges
                    )
            list.append(item)
        with plt.rc_context({'axes.edgecolor': 'gray'}):
            self._plot_correlograms_multi(list)

    def _plot_correlogram(self, ax, *, bin_counts, bin_edges, title=''):
        wid = (bin_edges[1] - bin_edges[0]) * 1000
        ax.bar(x=bin_edges[0:-1] * 1000, height=bin_counts, width=wid, color='gray', align='edge')
        ax.set_xlabel('dt (msec)')
        ax.set_xticks([])
        ax.set_yticks([])
        if title:
            ax.set_title(title, color='gray')

    def _plot_correlograms_multi(self, list, *, ncols=5, **kwargs):
        nrows = int(np.ceil(len(list) / ncols))
        if (self._figure is None) & (self._axs is None):
            f,axs = plt.subplots(nrows,ncols,figsize=(3 * ncols + 0.1, 3 * nrows + 0.1))
            self._figure = f
        for i, item in enumerate(list):
            ax = plt.subplot(nrows, ncols, i + 1)
            self._plot_correlogram(ax, **item, **kwargs)
        self._axs = axs

def compute_crosscorrelogram(x, y=None, *, max_dt_tp, bin_size_tp, max_samples=None):
    if y is None:
        y = x
        auto = True
    else: 
        auto = False
    if max_samples is not None:
        if max_samples < len(x):
            x = np.random.choice(x, size=max_samples, replace=False)
        if max_samples < len(y):
            y = np.random.choice(y, size=max_samples, replace=False)

    bin_start = -max_dt_tp
    bin_stop  = max_dt_tp
    bin_edges = np.arange(start=bin_start, stop=bin_stop+bin_size_tp, step=bin_size_tp)
    counts = np.zeros(len(bin_edges)-1)
    nbins = len(counts)
    x = np.sort(x)
    lx = len(x)-1
    y = np.sort(y)
    for yspk in y:
        xlo = np.searchsorted(x, yspk+bin_start) # find first spike of x within window relative to yspk
        xhi = np.searchsorted(x[xlo:], yspk+bin_stop, side='right')+xlo # find the last one
        xlo = max(0, xlo) # make sure they're in bounds
        xhi = min(lx, xhi)
        for i in np.arange(xlo,xhi):
            yspkdiff = x[i] - yspk # get time difference between events
            bin = min(np.searchsorted(bin_edges,yspkdiff), nbins) # get bin of time difference
            if ((yspkdiff == 0) & auto) | (bin == 0): # check bounds and exclude same event for autocorrelation
                continue
            counts[bin-1] += 1 # add to counts
    return (counts, bin_edges)


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

def test_crosscorrelogram():
    ## test 1
    offset = 2
    ans = spikeforest.spikewidgets.widgets.crosscorrelogramswidget.compute_crosscorrelogram(np.arange(1,400,25),
            np.arange(1+offset,400,25),
            max_dt_tp=20,
            bin_size_tp=0.1)
    ind = np.where(ans[0])
    assert ((ans[1][ind[0]] < offset ) & (ans[1][ind[0]+1] <= offset ))[0]

    ## test 2
    case = np.arange(1,400,15)
    counts1,edges1 = spikeforest.spikewidgets.widgets.crosscorrelogramswidget.compute_autocorrelogram(times,
            max_dt_tp=20, bin_size_tp=0.1)
    counts2,edges2 = spikeforest.spikewidgets.widgets.crosscorrelogramswidget.compute_crosscorrelogram(times,
            max_dt_tp=20, bin_size_tp=0.1)

    roughly_equals(counts1, counts2)

def roughly_equals():
    # TODO: implement
    return True


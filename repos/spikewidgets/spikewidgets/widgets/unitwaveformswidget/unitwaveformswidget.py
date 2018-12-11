from matplotlib import pyplot as plt
import numpy as np

class UnitWaveformsWidget:
    def __init__(self, *, recording, sorting, channels=None, unit_ids=None, width=14, height=7, snippet_len=100,
                 title='', max_num_spikes_per_unit=50):
        self._IX = recording
        self._OX = sorting
        self._channels = channels
        self._unit_ids = unit_ids
        self._width = width
        self._height = height
        self._figure = None
        self._snippet_len = snippet_len
        self._title = title
        self._max_num_spikes_per_unit = max_num_spikes_per_unit

    def plot(self):
        self._do_plot()

    def figure(self):
        return self._figure

    def _do_plot(self):
        units = self._unit_ids
        channels = self._channels
        if units is None:
            units = self._OX.getUnitIds()
        channel_ids = self._IX.getChannelIds()
        M = len(channel_ids)
        channel_locations = np.zeros((M, 2))
        for ii, ch in enumerate(channel_ids):
            loc = self._IX.getChannelProperty(ch, 'location')
            channel_locations[ii, :] = loc[-2:]
        if channels is None:
            channels = channel_ids
        list = []
        for unit in units:
            st = self._OX.getUnitSpikeTrain(unit_id=unit)
            if st is not None:
                spikes = self._get_random_spike_waveforms(unit=unit, max_num=self._max_num_spikes_per_unit,
                                                          channels=channels)
                item = dict(
                    representative_waveforms=spikes,
                    title='Unit {}'.format(int(unit))
                )
                list.append(item)
            else:
                print(unit, ' spike train is None')
        with plt.rc_context({'axes.edgecolor': 'gray'}):
            # self._plot_spike_shapes_multi(list,channel_locations=channel_locations[np.array(channels),:])
            self._plot_spike_shapes_multi(list, channel_locations=None)

    def _get_random_spike_waveforms(self, *, unit, max_num, channels):
        st = self._OX.getUnitSpikeTrain(unit_id=unit)
        num_events = len(st)
        if num_events > max_num:
            event_indices = np.random.choice(range(num_events), size=max_num, replace=False)
        else:
            event_indices = range(num_events)

        spikes = self._IX.getSnippets(reference_frames=st[event_indices].astype(int), snippet_len=self._snippet_len,
                                      channel_ids=channels)
        if len(spikes)>0:
            spikes = np.dstack(tuple(spikes))
        else:
            spikes = np.zeros((self._IX.getNumChannels(), self._snippet_len, 0))
        return spikes

    def _plot_spike_shapes(self, *, representative_waveforms=None, average_waveform=None, channel_locations=None,
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

        spacing = 1 / 0.8  # TODO: auto-determine this from the channel_locations

        xvals = np.linspace(-yrange / 2, yrange / 2, T)
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
                loc = channel_locations[m, -2:] * yrange * spacing
                for j in range(L):
                    XX[:, m, j] = loc[0] + xvals
                    YY[:, m, j] = loc[1] + representative_waveforms[m, :, j] - representative_waveforms[m, 0, j]
            XX = XX.reshape(T, M * L)
            YY = YY.reshape(T, M * L)
            plt.plot(XX, YY, color=(0.5, 0.5, 0.5), alpha=0.4)

            XX = np.zeros((T, M))
            YY = np.zeros((T, M))
            for m in range(M):
                loc = channel_locations[m, -2:] * yrange * spacing
                XX[:, m] = loc[0] + xvals
                YY[:, m] = loc[1] + average_waveform[m, :] - average_waveform[m, 0]
            plt.plot(XX, YY, color)

        plt.gca().get_xaxis().set_ticks([])
        plt.gca().get_yaxis().set_ticks([])
        if title:
            plt.title(title, color='gray')

    def _get_ylim_for_item(self, average_waveform=None, representative_waveforms=None):
        if average_waveform is None:
            if representative_waveforms is None:
                raise Exception('You must provide either average_waveform, representative waveforms, or both')
            average_waveform = np.mean(representative_waveforms, axis=2)
        return [average_waveform.min(), average_waveform.max()]

    def _determine_global_ylim(self, list):
        ret = [0, 0]
        for item in list:
            ylim0 = self._get_ylim_for_item(
                average_waveform=item.get('average_waveform', None),
                representative_waveforms=item.get('representative_waveforms', None)
            )
            ret[0] = np.minimum(ylim0[0], ret[0])
            ret[1] = np.maximum(ylim0[1], ret[1])
        return ret

    def _plot_spike_shapes_multi(self, list, *, ncols=5, **kwargs):
        if 'ylim' in kwargs:
            ylim = kwargs['ylim']
        else:
            ylim = self._determine_global_ylim(list)
        nrows = np.ceil(len(list) / ncols)
        self._figure = plt.figure(figsize=(3 * ncols + 0.1, 3 * nrows + 0.1))
        for i, item in enumerate(list):
            plt.subplot(nrows, ncols, i + 1)
            self._plot_spike_shapes(**item, **kwargs, ylim=ylim)

import uuid
from spikeforest import mdaio
import io
import base64
import vdomr as vd
import os
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
import numpy as np

class FeatureSpaceWidgetPlotly(vd.Component):
    def __init__(self, *, recording, sorting, channels=None, unit_ids=None, width=14, height=7, snippet_len=100,
                 title='', max_num_spikes_per_unit=1000):
        vd.Component.__init__(self)
        self._recording = recording
        self._sorting = sorting
        self._channels = channels
        self._unit_ids = unit_ids
        self._width = width
        self._height = height
        self._figure = None
        self._features = []
        self._snippet_len = snippet_len
        self._title = title
        self._max_num_spikes_per_unit = max_num_spikes_per_unit
        self._size=(800,500)
        self._do_compute()

    def setSize(self,size):
        if self._size==size:
            return
        self._size=size
        self.refresh()

    def render(self):
        data = []
        for ii, ff in enumerate(self._features):
            data.append(dict(
                x=ff[1,:].ravel(),
                y=ff[2,:].ravel(),
                mode = 'markers',
                name = 'Unit {}'.format(self._unit_ids[ii])
            ))
        plot=vd.components.PlotlyPlot(
            data = data,
            layout = dict(margin=dict(t=5)),
            config = dict(),
            size = self._size
        )
        return plot

    def plot(self):
        self._do_plot()

    def figure(self):
        return self._figure

    def _do_compute(self):
        units = self._unit_ids
        channels = self._channels
        if units is None:
            units = self._sorting.getUnitIds()
        channel_ids = self._recording.getChannelIds()
        M = len(channel_ids)
        channel_locations = np.zeros((M, 2))
        for ii, ch in enumerate(channel_ids):
            loc = self._recording.getChannelProperty(ch, 'location')
            channel_locations[ii, :] = loc[-2:]
        if channels is None:
            channels = channel_ids
        self._spike_waveforms_list = []
        for unit in units:
            st = self._sorting.getUnitSpikeTrain(unit_id=unit)
            if st is not None:
                spikes,spiketimes = self._get_random_spike_waveforms(unit=unit, max_num=self._max_num_spikes_per_unit,
                                                          channels=channels)
                item = dict(
                    representative_spiketimes=spiketimes,
                    representative_waveforms=spikes,
                    title='Unit {}'.format(int(unit))
                )
                self._spike_waveforms_list.append(item)
            else:
                print(unit, ' spike train is None')
        self._opts = {'channel':-1,
            'feature_extraction':'PCA',
            'features_to_show':(2,1)}
        self._get_spikes_in_feature_space_multi(self._spike_waveforms_list, self._opts)


    def _do_plot(self):
        self._do_compute()
        with plt.rc_context({'axes.edgecolor': 'gray'}):
            self._plot_spikes_in_feature_space_multi(self._spike_waveforms_list,self._opts)

    def _get_spikes_in_feature_space_multi(self,list,opts):
        channel = opts['channel']
        all_waveforms = None
        for spikes_dict in list:
            waveforms = spikes_dict['representative_waveforms']
            if channel == -1:
                s = np.shape(waveforms)
                spikes_dict['representative_waveforms'] = waveforms = waveforms.reshape(s[0]*s[1],s[2])
            else:
                spikes_dict['representative_waveforms'] = waveforms = waveforms[channel,:,:]
            if all_waveforms is None:
                all_waveforms = waveforms
            else:
                all_waveforms = np.concatenate([all_waveforms, waveforms], axis=1)
        feature_space = self._compute_features(all_waveforms, opts)
        for d in list:
            self._get_spikes_in_feature_space(d, feature_space, opts)

    def _get_spikes_in_feature_space(self, spikes_dict, feature_space, opts):
        waveforms  = spikes_dict['representative_waveforms']
        spiketimes = spikes_dict['representative_spiketimes']
        if not (np.shape(waveforms)[1] > 0):
            raise Exception('{} does not exist or has no spikes.'.format(spikes_dict['title']))
        features = feature_space.transform(waveforms.T).T
        spiketimes = (np.array(spiketimes)-np.max(spiketimes)/2)/2
        spiketimes.shape = (1,len(spiketimes))
        features = np.concatenate([spiketimes, features], axis=0)
        self._features.append(features)
        # TODO: Optionally exclude outliers

    def _plot_spikes_in_feature_space_multi(self,list,opts):
        features_to_show = opts['features_to_show']
        f = plt.figure(figsize=(10,10))
        for i,fet in enumerate(self._features):
            plt.scatter(fet[:,features_to_show[0]], fet[:,features_to_show[1]],
                    label=list[i]['title'])
        plt.legend()
        plt.xlabel('{} - {}'.format(opts['feature_extraction'], opts['features_to_show'][0]))
        plt.ylabel('{} - {}'.format(opts['feature_extraction'], opts['features_to_show'][1]))

    def _compute_features(self, spike_waveforms, opts):
        if opts['feature_extraction'] == 'PCA':
            features_obj = PCA()
            features_obj.fit(spike_waveforms.T)
        else:
            raise NotImplementedError('Override _compute_features if feature extraction other than PCA is required')
        return features_obj

    def _get_random_spike_waveforms(self, *, unit, max_num, channels):
        st = self._sorting.getUnitSpikeTrain(unit_id=unit)
        num_events = len(st)
        if num_events > max_num:
            event_indices = np.random.choice(range(num_events), size=max_num, replace=False)
        else:
            event_indices = range(num_events)

        spikes = self._recording.getSnippets(reference_frames=st[event_indices].astype(int), snippet_len=self._snippet_len,
                                      channel_ids=channels)
        if len(spikes)>0:
            spikes = np.dstack(tuple(spikes))
        else:
            spikes = np.zeros((self._recording.getNumChannels(), self._snippet_len, 0))
        return spikes, st[event_indices]


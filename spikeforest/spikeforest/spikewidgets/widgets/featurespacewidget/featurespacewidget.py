from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
import numpy as np

class FeatureSpaceWidget:
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
        print(np.shape(list[0]['representative_waveforms']))
        opts = {'channel':-1,
                'feature_extraction':'PCA',
                'features_to_show':(2,1)}
        with plt.rc_context({'axes.edgecolor': 'gray'}):
            # self._plot_spike_shapes_multi(list,channel_locations=channel_locations[np.array(channels),:])
            #self._plot_spike_shapes_multi(list, channel_locations=None)
            self._plot_spikes_in_feature_space_multi(list,opts)

    def _plot_spikes_in_feature_space(self, spikes_dict, feature_space, opts):
        features_to_show = opts['features_to_show']
        waveforms = spikes_dict['representative_waveforms']
        features = feature_space.transform(waveforms.T)
        # TODO: Optionally exclude outliers
        plt.scatter(features[:,features_to_show[0]], features[:,features_to_show[1]],
                label=spikes_dict['title'])

    def _plot_spikes_in_feature_space_multi(self,list,opts):
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

        f = plt.figure(figsize=(10,10))
        for d in list:
            self._plot_spikes_in_feature_space(d, feature_space, opts)
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

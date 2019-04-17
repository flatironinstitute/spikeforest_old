import uuid
from spikeforest import mdaio
import io
import base64
import vdomr as vd
import os
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
import numpy as np

source_path=os.path.dirname(os.path.realpath(__file__))

def _mda32_to_base64(X):
    f=io.BytesIO()
    mdaio.writemda32(X,f)
    return base64.b64encode(f.getvalue()).decode('utf-8')

class FeatureSpaceWidget(vd.Component):
    def __init__(self, *, recording, sorting, channels=None, unit_ids=None, width=14, height=7, snippet_len=100,
                 title='', max_num_spikes_per_unit=50):
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
        self._size=(100,100)

    def _init_js(self):
        vd.Component.__init__(self)

        vd.devel.loadBootstrap()
        vd.devel.loadCss(url='https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css')
        vd.devel.loadJavascript(path=source_path+'/mda.js')
        vd.devel.loadJavascript(path=source_path+'/featurespacemodel.js')
        vd.devel.loadJavascript(path=source_path+'/canvaswidget.js')
        vd.devel.loadJavascript(path=source_path+'/featurespacewidget.js')
        vd.devel.loadJavascript(path=source_path+'/../dist/jquery-3.3.1.min.js')

        self._div_id='SFFeatureSpaceWidget-'+str(uuid.uuid4())
	
        features = arr_to_js_string(self._features)

        js_lines=[
                "window.sfdata=window.sfdata||{}",
                "window.sfdata.test=0",
                "window.sfdata['features']={}".format(features)
                    ]
        js = ";".join(js_lines)
        vd.devel.loadJavascript(js=js)
        self._size=(800,400)

    def setSize(self,size):
        if self._size==size:
            return
        self._size=size
        self.refresh()

    def render(self):
        self._do_compute()
        self._init_js()
        div=vd.div(id=self._div_id)
        js="""
        let W=new window.FeatureSpaceWidget();
        let A=new window.Mda();
        W.setFeatures(window.sfdata['features']);
        W.setSize({width},{height})
        $('#{div_id}').empty();
        $('#{div_id}').css({width:'{width}px',height:'{height}px'})
        $('#{div_id}').append(W.element());
        """
        js=self._div_id.join(js.split('{div_id}'))
        js=js.replace('{width}',str(self._size[0]))
        js=js.replace('{height}',str(self._size[1]))
        js='{}'.format(self._recording.getSamplingFrequency()).join(js.split('{samplerate}'))
        vd.devel.loadJavascript(js=js,delay=1)
        return div

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

import re
def arr_to_js_string(arr):
    if not isinstance(arr[0],str):
        try:
            len(arr[0])
            return arr_to_js_string([arr_to_js_string(a) for a in arr])
        except TypeError:
            None
    js_string = '[{}]'.format(','.join(str(x) for x in arr))
    return js_string.replace("'", "")

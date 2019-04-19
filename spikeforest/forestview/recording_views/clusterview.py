import vdomr as vd
import time
import sys
import mtlogging
import numpy as np
from copy import deepcopy
from spikeforest import EfficientAccessRecordingExtractor
from numpy.linalg import svd

class ClusterView(vd.Component):
    def __init__(self, *, context, opts=None, prepare_result=None):
        vd.Component.__init__(self)
        self._context = context
        self._size = (100, 100)
        self._features = prepare_result['features']
        self._labels = prepare_result['labels']
        self._feature_names = prepare_result['feature_names']
        self._widget = ClusterWidget(features=self._features, labels=self._labels, feature_names=self._feature_names)
        self._widget.setSize(self._size)
        self.refresh()
    @staticmethod
    def prepareView(context, opts):
        sorting_context = context
        recording_context = context.recordingContext()
        sorting_context.initialize()

        sorting = sorting_context.sortingExtractor()

        unit_ids = sorting_context.selectedUnitIds()
        earx = EfficientAccessRecordingExtractor(recording=recording_context.recordingExtractor())

        M = earx.getNumChannels()
        T = 50
        K = len(unit_ids)
        num_features = 2

        spikes_list = []
        for unit_id in unit_ids:
            spikes = _get_random_spike_waveforms(sorting=sorting, recording=earx, unit=unit_id, max_num=50, channels=None, snippet_len=T)
            spikes_list.append(spikes)

        feature_waveforms = _get_feature_waveforms_for_spikes(spikes_list=spikes_list, num_features=num_features)
        # (num_features) x M x T
        features_list = []
        labels_list = []
        for ii, unit_id in enumerate(unit_ids):
            spikes0 = spikes_list[ii]
            features0 = np.reshape(feature_waveforms, (num_features, M*T)) @ np.reshape(spikes0, (M*T, spikes0.shape[2]))
            features_list.append(features0)
            labels_list.append(np.ones((features0.shape[1]))*unit_id)

        features = np.concatenate(features_list, axis=1)
        labels = np.concatenate(labels_list)
        return dict(
            features = features,
            labels = labels,
            feature_names = ['f{}'.format(i) for i in range(features.shape[0])]
        )

    def setSize(self, size):
        if self._size != size:
            self._size=size
        if self._widget:
            self._widget.setSize(size)

    def size(self):
        return self._size
    def tabLabel(self):
        return 'Clusters'
    def title(self):
        return 'Clusters for {}'.format(self._context.sortingLabel())
    def render(self):
        return self._widget

class ClusterWidget(vd.Component):
    def __init__(self, *, features, labels, feature_names):
        vd.Component.__init__(self)
        self._features = features
        self._labels = labels
        self._feature_names = feature_names
        self._size=(800,500)
        self._marker_size=14
        self._hover_marker_size=18
        self._plot=None

    def setSize(self,size):
        if self._size==size:
            return
        self._size=size
        if self._plot:
            self._plot.updateSize(size)

    def render(self):
        unit_ids = sorted(list(set(self._labels.tolist())))
        data = []
        for unit_id in unit_ids:
            ff = self._features[:,self._labels==unit_id]
            data.append(dict(
                x=ff[0,:].ravel(),
                y=ff[1,:].ravel(),
                mode = 'markers',
                name = 'Unit {}'.format(int(unit_id)),
                text = 'Unit {}'.format(int(unit_id)),
                hoverinfo='text',
                marker=dict(
                    size=self._marker_size,
                    line=dict(
                        color='white',
                        width=1
                    )
                )
            ))
        layout=dict(
            hovermode='closest'
        )
        config=dict(
            showTips=False,
            displayModeBar=True,
            displaylogo=False,
            modeBarButtonsToRemove=['hoverClosestCartesian','hoverCompareCartesian','resetScale2d']
        )
        self._plot=vd.components.PlotlyPlot(
            data = data,
            layout = layout,
            config = config,
            size = self._size
        )
        return self._plot
    def postRenderScript(self):
        js = """
        wait_for(function() {return {plotobj};}, 8, function() {
            {plotobj}.on('plotly_click', function(data){
                console.log('point clicked...', data);
            });
        });

        function wait_for(func, num_retries, cb) {
            if (func()) {
                cb();
                return;
            }
            if (num_retries<=0) return;
            setTimeout(function() {
                wait_for(func, num_retries-1, cb);
            },200);
        }
        """
        js=js.replace('{plotobj}', self._plot.javascriptPlotObject())
        #js=js.replace('{marker_size}', str(self._marker_size))
        #js=js.replace('{hover_marker_size}', str(self._hover_marker_size))
        return js
    def postRenderScript_struggling_with_hover(self):
        js = """
        setTimeout(function() {
            if ({plotobj}) {
                {plotobj}.on('plotly_hover', function(data){
                    try {
                        handle_hover(data, {hover_marker_size});
                    }
                    catch(err) {
                        console.error(err);
                        console.log('Warning: problem handling hover');
                    }
                });
                {plotobj}.on('plotly_unhover', function(data){
                    try {
                        handle_hover(data, {marker_size});
                    }
                    catch(err) {
                        console.error(err);
                        console.log('Warning: problem handling hover');
                    }
                });
                function handle_hover(data, marker_size) {
                    pt=data.points[0]
                    // color = pt.data.marker.color;
                    line = pt.data.marker.line;
                    let sizes=[];
                    for (let i=0; i<pt.data.x.length; i++)
                        sizes.push({marker_size});
                    sizes[pt.pointNumber]=marker_size;
                    Plotly.restyle({plotobj}, {marker:{size:sizes, line:line}}, [pt.curveNumber]);
                }
            }
        },100);
        """
        js=js.replace('{plotobj}', self._plot.javascriptPlotObject())
        js=js.replace('{marker_size}', str(self._marker_size))
        js=js.replace('{hover_marker_size}', str(self._hover_marker_size))
        return js

def _get_random_spike_waveforms(*, sorting, recording, unit, max_num, channels, snippet_len):
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

def _get_feature_waveforms_for_spikes(*, spikes_list, num_features):
    spikes0 = spikes_list[0]
    M = spikes0.shape[0]
    T = spikes0.shape[1]
    K = len(spikes_list)
    templates = np.zeros((M, T, K))
    for k in range(K):
        templates[:,:,k] = _compute_template_from_spikes(spikes_list[k])
    if K > 1:
        print(K)
        template0 = templates[:,:,0]
        templates2 = templates[:,:,1:] - np.repeat(template0[:,:,np.newaxis], K-1, axis=2)
        feature_waveforms1 = _get_feature_waveforms_helper(templates2, min(num_features, K-1))
        if num_features <= K-1:
            return feature_waveforms1[0:num_features,:,:]
    raise Exception('This case not yet supported')

def _get_feature_waveforms_helper(spikes, num_features):
    M = spikes.shape[0]
    T = spikes.shape[1]
    L = spikes.shape[2]
    template0=np.mean(spikes, axis=2)
    spikes2 = spikes - np.repeat(template0[:,:,np.newaxis], L, axis=2)
    U, _, _ = svd(np.reshape(spikes2, (M*T, L)), full_matrices=False)
    return np.reshape(U[:,0:num_features].T, (num_features, M, T))

def _compute_template_from_spikes(spikes):
    return np.median(spikes, axis=2)
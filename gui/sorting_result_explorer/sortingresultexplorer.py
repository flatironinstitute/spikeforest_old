import uuid
import json
from matplotlib import pyplot as plt
import numpy as np
import spikeextractors as se
from spikeforest import spiketoolkit as st
import spikeforestwidgets as SFW
import vdomr as vd
import os

ButtonList = SFW.sortingresultexplorer.ButtonList
ScrollArea = SFW.sortingresultexplorer.ScrollArea
ViewContainer = SFW.sortingresultexplorer.ViewContainer
TabBar = SFW.sortingresultexplorer.TabBar
Container = SFW.sortingresultexplorer.Container
ViewLauncher = SFW.sortingresultexplorer.ViewLauncher
VIEW_GeneralInfo = SFW.VIEW_GeneralInfo
VIEW_Timeseries = SFW.VIEW_Timeseries
VIEW_TrueUnitWaveforms = SFW.VIEW_TrueUnitWaveforms
VIEW_UnitWaveforms = SFW.VIEW_UnitWaveforms
VIEW_TrueAutocorrelograms = SFW.VIEW_TrueAutocorrelograms
VIEW_Autocorrelograms = SFW.VIEW_Autocorrelograms
VIEW_TrueUnitsTable = SFW.VIEW_TrueUnitsTable
Context = SFW.Context


CSS = """
.tabbartab {
  background-color:lightgray;
  padding:3px;
}
.tabbartab:hover {
  background-color:rgb(240,240,240);
}
.tabbartab.selected {
  background-color:white;
  color:green;
}
"""

UnitWaveformWidget = SFW.UnitWaveformWidget


def get_unmatched_times(times1, times2, *, delta):
    # spikes in first sorting that are not matched to spikes in second sorting
    times1 = np.array(times1)
    times2 = np.array(times2)
    times_concat = np.concatenate((times1, times2))
    membership = np.concatenate(
        (np.ones(times1.shape) * 1, np.ones(times2.shape) * 2))
    indices = times_concat.argsort()
    times_concat_sorted = times_concat[indices]
    membership_sorted = membership[indices]
    diffs = times_concat_sorted[1:] - times_concat_sorted[:-1]
    unmatched_inds = 1 + \
        np.where((diffs[1:] > delta) & (diffs[:-1] > delta)
                 & (membership_sorted[1:-1] == 1))[0]
    if (diffs[0] > delta) and (membership_sorted[0] == 1):
        unmatched_inds = np.concatenate(([0], unmatched_inds))
    if (diffs[-1] > delta) and (membership_sorted[-1] == 1):
        unmatched_inds = np.concatenate(
            (unmatched_inds, [len(membership_sorted)-1]))
    return times_concat_sorted[unmatched_inds]


def get_unmatched_sorting(sx1, sx2, ids1, ids2):
    # spikes in first sorting that are not matched to spikes in second sorting
    ret = se.NumpySortingExtractor()
    for ii in range(len(ids1)):
        id1 = ids1[ii]
        id2 = ids2[ii]
        train1 = sx1.getUnitSpikeTrain(unit_id=id1)
        train2 = sx2.getUnitSpikeTrain(unit_id=id2)
        train = get_unmatched_times(train1, train2, delta=100)
        ret.addUnit(id1, train)
    return ret


def _get_random_spike_waveforms(*, recording, sorting, unit, max_num=50, channels=None, snippet_len=100):
    st = sorting.getUnitSpikeTrain(unit_id=unit)
    num_events = len(st)
    if num_events > max_num:
        event_indices = np.random.choice(
            range(num_events), size=max_num, replace=False)
    else:
        event_indices = range(num_events)

    spikes = recording.getSnippets(reference_frames=st[event_indices].astype(int), snippet_len=snippet_len,
                                   channel_ids=channels)
    if len(spikes) > 0:
        spikes = np.dstack(tuple(spikes))
    else:
        spikes = np.zeros((recording.getNumChannels(), snippet_len, 0))
    return spikes


def _compute_average_waveform(recording, sorting, *, unit, max_num=50, channels=None, snippet_len=100):
    snippets = _get_random_spike_waveforms(
        recording=recording, sorting=sorting, unit=unit, max_num=max_num, channels=channels, snippet_len=snippet_len)
    ret = np.mean(snippets, axis=2)
    return ret


class VIEW_SelectedTrueUnitComparison(vd.Component):
    LABEL = 'Selected true unit comparison'

    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        ids = self._context.selectedTrueUnitIds()
        self._size = (300, 300)
        self._error_message = None
        if len(ids) != 1:
            self._error_message = 'You must select exactly one true unit ({} selected).'.format(
                len(ids))
            return
        self._true_unit_id = ids[0]
        true_units_info = self._context.recording.trueUnitsInfo(format='json')
        self._true_unit_info = None
        for i, info in enumerate(true_units_info):
            if info['unit_id'] == self._true_unit_id:
                self._true_unit_info = info
        if self._true_unit_info is None:
            self._error_message = 'Unable to find info for true unit {}'.format(
                self._true_unit_id)
            return
        comparison_info = self._context.sorting_result.comparisonWithTruth(
            format='json')
        self._true_unit_comparison_info = None
        for i in comparison_info:
            info = comparison_info[i]
            if info['unit_id'] == self._true_unit_id:
                self._true_unit_comparison_info = info
        if self._true_unit_comparison_info is None:
            self._error_message = 'Unable to find comparison info for true unit {}'.format(
                self._true_unit_id)
            return
        self._sorted_unit_id = self._true_unit_comparison_info['best_unit']
        rx = self._context.recording.recordingExtractor()
        sf = rx.getSamplingFrequency()
        rx = st.preprocessing.bandpass_filter(
            recording=rx, freq_min=300, freq_max=6000)
        sx_true = self._context.recording.sortingTrue()
        sx_sorted = self._context.sorting_result.sorting()
        sx_unmatched_true = get_unmatched_sorting(
            sx_true, sx_sorted, [self._true_unit_id], [self._sorted_unit_id])
        sx_unmatched_sorted = get_unmatched_sorting(
            sx_sorted, sx_true, [self._sorted_unit_id], [self._true_unit_id])
        snippet_len = 80
        average_waveform = _compute_average_waveform(
            rx, sx_true, unit=self._true_unit_id, max_num=50, snippet_len=snippet_len)
        args = dict(
            recording=rx,
            average_waveform=average_waveform,
            snippet_len=snippet_len,
            show_average=False,
            max_num_spikes_per_unit=12
        )
        self._true_unit_waveform_widget = UnitWaveformWidget(
            **args, sorting=sx_true, unit_id=self._true_unit_id)
        self._sorted_unit_waveform_widget = UnitWaveformWidget(
            **args, sorting=sx_sorted, unit_id=self._sorted_unit_id)
        self._unmatched_true_unit_waveform_widget = UnitWaveformWidget(
            **args, sorting=sx_unmatched_true, unit_id=self._true_unit_id)
        self._unmatched_sorted_unit_waveform_widget = UnitWaveformWidget(
            **args, sorting=sx_unmatched_sorted, unit_id=self._sorted_unit_id)

    def tabLabel(self):
        if self._error_message:
            return 'Error'
        return 'True unit {}'.format(self._true_unit_id)

    def setSize(self, size):
        self._size = size
        self.refresh()

    def render(self):
        if self._error_message:
            return vd.div(self._error_message)
        box_style = dict(float='left')
        boxes = [
            vd.div(W, style=box_style)
            for W in [
                self._true_unit_waveform_widget,
                self._sorted_unit_waveform_widget,
                self._unmatched_true_unit_waveform_widget,
                self._unmatched_sorted_unit_waveform_widget
            ]
        ]
        div = vd.div(
            vd.h3('True unit {}, Sorted unit {}'.format(
                self._true_unit_id, self._sorted_unit_id)),
            vd.div(boxes)

        )
        return ScrollArea(div, size=self._size)


def _compute_principal_components(X, num_components):
    u, s, vt = np.linalg.svd(X)
    u = u[:, :num_components]
    return u


class VIEW_SelectedTrueUnitComparison2(vd.Component):
    LABEL = 'Selected true unit comparison 2'

    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        ids = self._context.selectedTrueUnitIds()
        self._size = (300, 300)
        self._error_message = None
        if len(ids) != 1:
            self._error_message = 'You must select exactly one true unit ({} selected).'.format(
                len(ids))
            return
        self._true_unit_id = ids[0]
        true_units_info = self._context.recording.trueUnitsInfo(format='json')
        self._true_unit_info = None
        for i, info in enumerate(true_units_info):
            if info['unit_id'] == self._true_unit_id:
                self._true_unit_info = info
        if self._true_unit_info is None:
            self._error_message = 'Unable to find info for true unit {}'.format(
                self._true_unit_id)
            return
        comparison_info = self._context.sorting_result.comparisonWithTruth(
            format='json')
        self._true_unit_comparison_info = None
        for i in comparison_info:
            info = comparison_info[i]
            if info['unit_id'] == self._true_unit_id:
                self._true_unit_comparison_info = info
        if self._true_unit_comparison_info is None:
            self._error_message = 'Unable to find comparison info for true unit {}'.format(
                self._true_unit_id)
            return
        self._sorted_unit_id = self._true_unit_comparison_info['best_unit']
        rx = self._context.recording.recordingExtractor()
        sf = rx.getSamplingFrequency()
        rx = st.preprocessing.bandpass_filter(
            recording=rx, freq_min=300, freq_max=6000)
        sx_true = self._context.recording.sortingTrue()
        sx_sorted = self._context.sorting_result.sorting()
        sx_unmatched_true = get_unmatched_sorting(
            sx_true, sx_sorted, [self._true_unit_id], [self._sorted_unit_id])
        sx_unmatched_sorted = get_unmatched_sorting(
            sx_sorted, sx_true, [self._sorted_unit_id], [self._true_unit_id])
        snippet_len = 80

        channel_ids = rx.getChannelIds()

        snippets1 = _get_random_spike_waveforms(
            recording=rx, sorting=sx_true, unit=self._true_unit_id, max_num=250, snippet_len=snippet_len, channels=channel_ids)
        snippets2 = _get_random_spike_waveforms(
            recording=rx, sorting=sx_unmatched_true, unit=self._true_unit_id, max_num=250, snippet_len=snippet_len, channels=channel_ids)
        snippets3 = _get_random_spike_waveforms(
            recording=rx, sorting=sx_unmatched_sorted, unit=self._sorted_unit_id, max_num=250, snippet_len=snippet_len, channels=channel_ids)
        components = _compute_principal_components(snippets1.reshape(
            (snippets1.shape[0]*snippets1.shape[1], snippets1.shape[2])), num_components=2)
        features1 = components.transpose() @ snippets1.reshape(
            (snippets1.shape[0]*snippets1.shape[1], snippets1.shape[2]))
        features2 = components.transpose() @ snippets2.reshape(
            (snippets2.shape[0]*snippets2.shape[1], snippets2.shape[2]))
        features3 = components.transpose() @ snippets3.reshape(
            (snippets3.shape[0]*snippets3.shape[1], snippets3.shape[2]))
        features = np.concatenate((features1, features2, features3), axis=1)
        labels = np.concatenate(
            (1*np.ones(features1.shape[1]), 2*np.ones(features2.shape[1]), 3*np.ones(features3.shape[1])))

        class _ClusterPlot(vd.components.Pyplot):
            def __init__(self, *, features, labels):
                vd.components.Pyplot.__init__(self)
                self._features = features
                self._labels = labels

            def plot(self):
                plt.scatter(
                    self._features[0, :], self._features[1, :], marker='.', c=self._labels)
        self._widget = _ClusterPlot(features=features, labels=labels)

    def tabLabel(self):
        if self._error_message:
            return 'Error'
        return 'True unit {} (2)'.format(self._true_unit_id)

    def setSize(self, size):
        self._size = size
        self._widget.setSize((self._size[0]-20, self._size[1]-20))
        self.refresh()

    def render(self):
        if self._error_message:
            return vd.div(self._error_message)
        return vd.div(self._widget)


class ControlPanel(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context

        general_view_classes = [VIEW_GeneralInfo,
                                VIEW_Timeseries, VIEW_TrueUnitsTable]
        truth_view_classes = [
            VIEW_TrueUnitWaveforms, VIEW_TrueAutocorrelograms]
        sorting_view_classes = [VIEW_UnitWaveforms, VIEW_Autocorrelograms]
        comparison_view_classes = [VIEW_SelectedTrueUnitComparison,
                                   VIEW_SelectedTrueUnitComparison2, VIEW_SelectedTrueUnitComparison3]

        self._general_view_launcher = ViewLauncher(
            context, general_view_classes)
        self._truth_view_launcher = ViewLauncher(context, truth_view_classes)
        self._sorting_view_launcher = ViewLauncher(
            context, sorting_view_classes)
        self._comparison_view_launcher = ViewLauncher(
            context, comparison_view_classes)

        self._view_launchers = [
            self._general_view_launcher,
            self._truth_view_launcher,
            self._sorting_view_launcher,
            self._comparison_view_launcher
        ]

    def onLaunchView(self, handler):
        for VL in self._view_launchers:
            VL.onLaunchView(handler)

    def render(self):
        return vd.div(
            vd.h3('General'),
            self._general_view_launcher,
            vd.h3('Ground truth'),
            self._truth_view_launcher,
            vd.h3('Sorting'),
            self._sorting_view_launcher,
            vd.h3('Comparison'),
            self._comparison_view_launcher
        )


class SortingResultExplorer(vd.Component):
    def __init__(self, sorting_result):
        vd.Component.__init__(self)

        self._context = Context()
        self._context.sorting_result = sorting_result
        self._context.recording = sorting_result.recording()
        self._control_panel = ControlPanel(self._context)
        self._view_container_north = ViewContainer()
        self._view_container_south = ViewContainer()
        self._control_panel.onLaunchView(self._on_launch_view)

        self._current_view_container = self._view_container_north
        self._view_container_north.onClick(self._on_click_north)
        self._view_container_south.onClick(self._on_click_south)

        self._highlight_view_containers()

        vd.devel.loadBootstrap()
        vd.devel.loadCss(css=CSS)

        self._context.onSelectionChanged(self._on_selection_changed)

    def _highlight_view_containers(self):
        for VC in [self._view_container_north, self._view_container_south]:
            VC.setHighlight(VC == self._current_view_container)

    def _on_click_north(self):
        self._current_view_container = self._view_container_north
        self._highlight_view_containers()

    def _on_click_south(self):
        self._current_view_container = self._view_container_south
        self._highlight_view_containers()

    def _on_launch_view(self, view_class):
        V = view_class(self._context)
        self._current_view_container.addView(V)

    def _on_selection_changed(self):
        pass

    def context(self):
        return self._context

    def render(self):
        width = 1400
        width1 = 300
        width2 = width-width1-10
        height = 700
        height1 = int(height/2)-5
        height2 = height-height1-10
        style0 = dict(border='solid 1px gray')
        W_CP = Container(self._control_panel, position=(
            0, 0), size=(width1, height), style=style0)
        self._view_container_north.setSize((width2, height1))
        self._view_container_south.setSize((width2, height2))
        W_VCN = Container(self._view_container_north, position=(
            width1+10, 0), size=(width2, height1), style=style0)
        W_VCS = Container(self._view_container_south, position=(
            width1+10, height1+10), size=(width2, height2), style=style0)
        return Container(W_CP, W_VCN, W_VCS, position=(0, 0), size=(width, height), position_mode='relative')


class SpikeWaveformsWidget(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._elmt_id = str(uuid.uuid4())
        self._size = [200, 200]
        self._geometry = None
        self._spikes = None
        basepath = os.environ['SIMPLOT_SRC_DIR']
        vd.devel.loadJavascript(path=basepath+'/jquery-3.3.1.min.js')
        vd.devel.loadJavascript(path=basepath+'/d3.min.js')
        vd.devel.loadJavascript(path=basepath+'/simplot.js')
        vd.devel.loadJavascript(path=basepath+'/spikeforestwidgets.js')

    def setSize(self, W, H):
        self._size = [W, H]
        self.refresh()

    def size(self):
        return self._size

    def setGeometry(self, geom):
        self._geometry = geom
        self.refresh()

    def setSpikes(self, spikes):
        self._spikes = spikes
        self.refresh()

    def render(self):
        if self._geometry is None:
            return vd.div('geometry not set')
        if self._spikes is None:
            return vd.div('spikes not set')
        div = vd.div(id=self._elmt_id)
        js = """
      function wait_for_ready(cb) {
        if ((window.d3)&&(window.Simplot)&&(window.SpikeforestWidgets)&&(document.getElementById('{elmt_id}'))) cb();
        else setTimeout(function() {wait_for_ready(cb);},10);
      }
      wait_for_ready(function() {
        let SpikeWaveformsWidget=window.SpikeforestWidgets.SpikeWaveformsWidget;
        let div=document.getElementById('{elmt_id}');
        $(div).empty();
        let W=new SpikeWaveformsWidget(div);
        W.setSize({width},{height});
        W.setGeometry(JSON.parse('{geom}'))
        let spikes=JSON.parse('{spikes}');
        for (let i=0; i<spikes.length; i++) {
          W.addSpike('spike-'+i,spikes[i]);
        }
        /*
        let geom=[[0.5,1],[1.5,1],[0,0],[1,0],[2,0],[0.5,-1],[1.5,-1]];
        W.setGeometry(geom);
        let num_channels=geom.length;
        let tmp1=[0,1,2,3,4,6,12,20,12,6,4,3,2,1,0];
        let tmp2=[0,1,2,3,4,6,12,5,12,6,4,3,2,1,0];
        let data=[tmp1,tmp2,tmp2,tmp2,tmp2,tmp2,tmp2,tmp2];
        let noise_level=5;
        let num_spikes=35;
        for (let i=0; i<num_spikes; i++) {
          let data0=[];
          for (let m=0; m<num_channels; m++) {
            data0.push(data[m].map(function(v) {return v+Math.random()*noise_level;}));
          }
          W.addSpike('spike-'+i,data0);
        }
        */
      });
    """
        js = js.replace('{elmt_id}', self._elmt_id)
        js = js.replace('{width}', '{}'.format(self._size[0]))
        js = js.replace('{height}', '{}'.format(self._size[1]))
        js = js.replace('{geom}', json.dumps(self._geometry))
        spikes = []
        for spike0 in self._spikes:
            a = []
            for m in range(spike0.shape[0]):
                a.append(spike0[m, :].tolist())
            spikes.append(a)
        js = js.replace('{spikes}', json.dumps(spikes))
        # def array_to_json(X):
        #  return json.dumps([str(v) for v in np.array(X).tolist()])
        # x0=array_to_json(self._x)
        # y0=array_to_json(self._y)
        # js=js.replace('{x}',x0)
        # js=js.replace('{y}',y0)
        vd.devel.loadJavascript(js=js, delay=0)
        return div


def _get_random_spike_waveforms(*, recording, sorting, unit, max_num, channels, snippet_len):
    st = sorting.getUnitSpikeTrain(unit_id=unit)
    num_events = len(st)
    if num_events > max_num:
        event_indices = np.random.choice(
            range(num_events), size=max_num, replace=False)
    else:
        event_indices = range(num_events)

    spikes = recording.getSnippets(reference_frames=st[event_indices].astype(int), snippet_len=snippet_len,
                                   channel_ids=channels)
    if len(spikes) > 0:
        spikes = np.dstack(tuple(spikes))
    else:
        spikes = np.zeros((recording.getNumChannels(), snippet_len, 0))
    return spikes


class UnitWaveformWidget2(vd.Component):
    def __init__(self, *, recording, sorting, unit_id, average_waveform=None, show_average=True, max_num_spikes_per_unit=20, snippet_len=100):
        vd.Component.__init__(self)

        channel_ids = recording.getChannelIds()
        M = len(channel_ids)
        geom = []
        for ii, ch in enumerate(channel_ids):
            loc = recording.getChannelProperty(ch, 'location')
            geom.append([loc[-2], loc[-1]])

        spikes = _get_random_spike_waveforms(recording=recording, sorting=sorting, unit=unit_id,
                                             max_num=max_num_spikes_per_unit, channels=channel_ids, snippet_len=snippet_len)
        spikes = [spikes[:, :, i] for i in range(spikes.shape[2])]

        self._plot = SpikeWaveformsWidget()
        self._plot.setSize(200, 200)
        self._plot.setGeometry(geom)
        self._plot.setSpikes(spikes)
        self._plot_div = vd.components.LazyDiv(self._plot)

    def render(self):
        style0 = {'border': 'solid 1px black', 'margin': '5px'}
        style1 = {}
        # if self._selected:
        #    style1['background-color']='yellow'
        return vd.div(
            vd.p('Title'),
            vd.div(self._plot_div, style=style0),
            style=style1
        )


class VIEW_SelectedTrueUnitComparison3(vd.Component):
    LABEL = 'Selected true unit comparison 3'

    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        ids = self._context.selectedTrueUnitIds()
        self._size = (300, 300)
        self._error_message = None
        if len(ids) != 1:
            self._error_message = 'You must select exactly one true unit ({} selected).'.format(
                len(ids))
            return
        self._true_unit_id = ids[0]
        true_units_info = self._context.recording.trueUnitsInfo(format='json')
        self._true_unit_info = None
        for i, info in enumerate(true_units_info):
            if info['unit_id'] == self._true_unit_id:
                self._true_unit_info = info
        if self._true_unit_info is None:
            self._error_message = 'Unable to find info for true unit {}'.format(
                self._true_unit_id)
            return
        comparison_info = self._context.sorting_result.comparisonWithTruth(
            format='json')
        self._true_unit_comparison_info = None
        for i in comparison_info:
            info = comparison_info[i]
            if info['unit_id'] == self._true_unit_id:
                self._true_unit_comparison_info = info
        if self._true_unit_comparison_info is None:
            self._error_message = 'Unable to find comparison info for true unit {}'.format(
                self._true_unit_id)
            return
        self._sorted_unit_id = self._true_unit_comparison_info['best_unit']
        rx = self._context.recording.recordingExtractor()
        sf = rx.getSamplingFrequency()
        rx = st.preprocessing.bandpass_filter(
            recording=rx, freq_min=300, freq_max=6000)
        sx_true = self._context.recording.sortingTrue()
        sx_sorted = self._context.sorting_result.sorting()
        sx_unmatched_true = get_unmatched_sorting(
            sx_true, sx_sorted, [self._true_unit_id], [self._sorted_unit_id])
        sx_unmatched_sorted = get_unmatched_sorting(
            sx_sorted, sx_true, [self._sorted_unit_id], [self._true_unit_id])
        snippet_len = 80
        average_waveform = _compute_average_waveform(
            rx, sx_true, unit=self._true_unit_id, max_num=50, snippet_len=snippet_len)
        args = dict(
            recording=rx,
            average_waveform=average_waveform,
            snippet_len=snippet_len,
            show_average=False,
            max_num_spikes_per_unit=12
        )
        self._true_unit_waveform_widget = UnitWaveformWidget2(
            **args, sorting=sx_true, unit_id=self._true_unit_id)
        self._sorted_unit_waveform_widget = UnitWaveformWidget2(
            **args, sorting=sx_sorted, unit_id=self._sorted_unit_id)
        self._unmatched_true_unit_waveform_widget = UnitWaveformWidget2(
            **args, sorting=sx_unmatched_true, unit_id=self._true_unit_id)
        self._unmatched_sorted_unit_waveform_widget = UnitWaveformWidget2(
            **args, sorting=sx_unmatched_sorted, unit_id=self._sorted_unit_id)

    def tabLabel(self):
        if self._error_message:
            return 'Error'
        return 'True unit {}'.format(self._true_unit_id)

    def setSize(self, size):
        self._size = size
        self.refresh()

    def render(self):
        if self._error_message:
            return vd.div(self._error_message)
        box_style = dict(float='left')
        boxes = [
            vd.div(W, style=box_style)
            for W in [
                self._true_unit_waveform_widget,
                self._sorted_unit_waveform_widget,
                self._unmatched_true_unit_waveform_widget,
                self._unmatched_sorted_unit_waveform_widget
            ]
        ]
        div = vd.div(
            vd.h3('True unit {}, Sorted unit {}'.format(
                self._true_unit_id, self._sorted_unit_id)),
            vd.div(boxes)
        )
        return ScrollArea(div, size=self._size)

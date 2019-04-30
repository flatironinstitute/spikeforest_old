from .spikeforest_views.currentstateview import CurrentStateView
from .spikeforest_views.recordingtableview import RecordingTableView, RecordingSelectComponent
from .spikeforest_views.aggregatedsortingresultstableview import AggregatedSortingResultsTableView
from .recording_views.electrodegeometryview import ElectrodeGeometryView
from .recording_views.timeseriesview import TimeseriesView
from .recording_views.templatesview import TemplatesView
from .recording_views.recordingsummaryview import RecordingSummaryView
from .recording_views.unitstableview import UnitsTableView
from .recording_views.sortingresultstableview import SortingResultsTableView, SortingResultSelectComponent
from .recording_views.sortingresultdetailview import SortingResultDetailView
from .recording_views.featurespaceview import FeatureSpaceView
from .recording_views.clusterview import ClusterView

import vdomr as vd
from mountaintools import client as mt
import json

def get_spikeforest_view_launchers(context):
    launchers=[]
    groups=[]
    ret = dict(
        groups=groups,
        launchers=launchers
    )

    # General
    groups.append(dict(name='general',label=''))

    launchers.append(dict(
        group='general', name='recording-table', label='Recording table',
        view_class=RecordingTableView,
        context=context, opts=dict(),
        enabled=True
    ))
    launchers.append(dict(
        group='general', name='current-state', label='Current state',
        view_class=CurrentStateView,
        context=context, opts=dict(),
        enabled=True
    ))
    # MEDIUM TODO: this should be a component rather than a launcher
    launchers.append(dict(
        group='general', name='recording-select',
        component_class=RecordingSelectComponent,
        context=context, opts=dict(),
        enabled=True
    ))
    
    recording_context = context.recordingContext(context.currentRecordingId())

    # Aggregated sorting results
    if context.hasAggregatedSortingResults():
        groups.append(dict(name='aggregated_sorting_results',label='Aggregated results'))

        launchers.append(dict(
            group='aggregated_sorting_results', name='aggregated-results-table', label='Results table',
            view_class=AggregatedSortingResultsTableView,
            context=context, opts=dict(),
            always_open_new=False,
            enabled=True
        ))

    # Recording
    if recording_context:
        groups.append(dict(name='recording',label='Recording',sublabel=context.currentRecordingId()))
    
        launchers.append(dict(
            group='recording', name='recording-summary', label='Recording summary',
            view_class=RecordingSummaryView,
            context=recording_context, opts=dict(),
            always_open_new=True,
            enabled=(recording_context is not None)
        ))
        launchers.append(dict(
            group='recording', name='electrode-geometry', label='Electrode geometry',
            view_class=ElectrodeGeometryView,
            context=recording_context, opts=dict(),
            enabled=(recording_context is not None)
        ))
        launchers.append(dict(
            group='recording', name='timeseries', label='Timeseries',
            view_class=TimeseriesView,
            context=recording_context, opts=dict(),
            always_open_new=True,
            enabled=(recording_context is not None)
        ))
        if recording_context.hasIntraRecording():
            launchers.append(dict(
                group='recording', name='intra-timeseries', label='Intra-timeseries',
                view_class=TimeseriesView,
                context=recording_context.intraRecordingContext(),
                always_open_new=True,
                enabled=(recording_context is not None)
            ))

    # True sorting
    if recording_context and recording_context.trueSortingContext():
        true_sorting_context = recording_context.trueSortingContext()

        groups.append(dict(name='true-sorting',label='True sorting'))
        launchers.append(dict(
            group='true-sorting', name='true-templates', label='Templates',
            view_class=TemplatesView,
            context=true_sorting_context, opts=dict(),
            always_open_new=True,
            enabled=(true_sorting_context is not None)
        ))
        launchers.append(dict(
            group='true-sorting', name='true-units-info', label='Units info',
            view_class=UnitsTableView,
            context=true_sorting_context, opts=dict(),
            always_open_new=True,
            enabled=(true_sorting_context is not None)
        ))
        launchers.append(dict(
            group='true-sorting', name='feature-space', label='Feature space',
            view_class=FeatureSpaceView,
            context=true_sorting_context, opts=dict(),
            always_open_new=True,
            enabled=(len(true_sorting_context.selectedUnitIds()) > 0)
        ))
        launchers.append(dict(
            group='true-sorting', name='clusters', label='Clusters',
            view_class=ClusterView,
            context=true_sorting_context, opts=dict(),
            always_open_new=True,
            enabled=(len(true_sorting_context.selectedUnitIds()) > 0)
        ))
    
        dict(name='unit',label='Unit')
        launchers.append(dict(
            group='true-sorting', name='test', label='Test',
            view_class=TemplatesView,
            context=true_sorting_context, opts=dict(),
            always_open_new=True,
            enabled=(true_sorting_context.currentUnitId() is not None)
        ))

    # Sorting results
    if recording_context and (len(recording_context.sortingResultNames()) > 0):
        groups.append(dict(name='sorting-results',label='Sorting results'))
        launchers.append(dict(
            group='sorting-results', name='sorting-results-table', label='Sorting results table',
            view_class=SortingResultsTableView,
            context=recording_context, opts=dict(),
            always_open_new=True,
            enabled=(len(recording_context.sortingResultNames()) > 0)
        ))
        launchers.append(dict(
            group='sorting-results', name='sorting-result-select',
            component_class=SortingResultSelectComponent,
            context=recording_context, opts=dict(),
            always_open_new=True,
            enabled=(len(recording_context.sortingResultNames()) > 0)
        ))

    # Sorting result
    if recording_context and recording_context.currentSortingResult():
        srname = recording_context.currentSortingResult()
        sorting_result_context = recording_context.sortingResultContext(srname)

        groups.append(dict(name='sorting-result',label='Sorting result',sublabel=srname))
        launchers.append(dict(
            group='sorting-result', name='sorting-result-details', label='Details',
            view_class=SortingResultDetailView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(sorting_result_context is not None)
        ))
        launchers.append(dict(
            group='sorting-result', name='templates', label='Templates',
            view_class=TemplatesView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(sorting_result_context is not None)
        ))
        launchers.append(dict(
            group='sorting-result', name='units-info', label='Units info',
            view_class=UnitsTableView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(sorting_result_context is not None)
        ))
        launchers.append(dict(
            group='sorting-result', name='feature-space', label='Feature space',
            view_class=FeatureSpaceView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(len(sorting_result_context.selectedUnitIds()) > 0)
        ))
        launchers.append(dict(
            group='sorting-result', name='clusters', label='Clusters',
            view_class=ClusterView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(len(sorting_result_context.selectedUnitIds()) > 0)
        ))
        launchers.append(dict(
            group='sorting-result', name='console-out', label='Console output',
            view_class=ConsoleOutView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(sorting_result_context.consoleOutputPath() is not None)
        ))
        launchers.append(dict(
            group='sorting-result', name='exec-stats', label='Execution stats',
            view_class=ExecutionStatsView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(sorting_result_context.executionStats() is not None)
        ))
        launchers.append(dict(
            group='sorting-result', name='comparison-with-truth', label='Comparison with truth',
            view_class=ComparisonWithTruthView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(sorting_result_context.comparisonWithTruthPath() is not None)
        ))
    
        dict(name='unit',label='Unit')
        launchers.append(dict(
            group='sorting-result', name='test', label='Test',
            view_class=TemplatesView,
            context=sorting_result_context, opts=dict(),
            always_open_new=True,
            enabled=(sorting_result_context.currentUnitId() is not None)
        ))
    
    
    return ret

class ConsoleOutView(vd.Component):
    def __init__(self, *, context, opts=None):
        vd.Component.__init__(self)
        self._context = context
        self._size = (100, 100)
        if not context.consoleOutputPath():
            self._text = 'no console output found'
        else:
            self._text = mt.loadText(path=context.consoleOutputPath()) or 'unable to load console output'

    def setSize(self, size):
        if self._size != size:
            self._size=size
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Console out'
    def render(self):
        return vd.components.ScrollArea(vd.pre(self._text), height=self._size[1])

class ExecutionStatsView(vd.Component):
    def __init__(self, *, context, opts=None):
        vd.Component.__init__(self)
        self._context = context
        self._size = (100, 100)
        self._stats = context.executionStats()

    def setSize(self, size):
        if self._size != size:
            self._size=size
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Exec stats'
    def render(self):
        if not self._stats:
            return vd.div('No stats found')
        return vd.div(vd.pre(json.dumps(self._stats, indent=4)))


class ComparisonWithTruthView(vd.Component):
    def __init__(self, *, context, opts=None):
        vd.Component.__init__(self)
        self._context = context
        self._size = (100, 100)
        if not context.comparisonWithTruthPath():
            self._object = None
        else:
            self._object = mt.loadObject(path=context.comparisonWithTruthPath())

    def setSize(self, size):
        if self._size != size:
            self._size=size
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Comparison with truth'
    def render(self):
        if not self._object:
            return vd.div('Unable to load comparison data.')
        return vd.components.ScrollArea(vd.pre(json.dumps(self._object,indent=4)), height=self._size[1])
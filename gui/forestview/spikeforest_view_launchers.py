from spikeforest_views.currentstateview import CurrentStateView
from spikeforest_views.recordingtableview import RecordingTableView
from recording_views.electrodegeometryview import ElectrodeGeometryView
from recording_views.timeseriesview import TimeseriesView
from recording_views.templatesview import TemplatesView
from recording_views.recordingsummaryview import RecordingSummaryView
from recording_views.unitstableview import UnitsTableView

def get_spikeforest_view_launchers(context):
    launchers=[]
    ret = dict(
        groups=[
            dict(name='general',label=''),
            dict(name='recording',label='Recording'),
            dict(name='unit',label='Unit')
        ],
        launchers=launchers
    )
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
    
    recording_context=context.recordingContext(context.currentRecordingId())

    launchers.append(dict(
        group='recording', name='recording-summary', label='Recording summary',
        view_class=RecordingSummaryView,
        context=recording_context, opts=dict(),
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
        enabled=(recording_context is not None)
    ))
    launchers.append(dict(
        group='recording', name='true-templates', label='Templates (true)',
        view_class=TemplatesView,
        context=recording_context, opts=dict(),
        enabled=(recording_context is not None)
    ))
    launchers.append(dict(
        group='recording', name='true-units-info', label='Units info (true)',
        view_class=UnitsTableView,
        context=recording_context, opts=dict(),
        enabled=(recording_context is not None)
    ))
    launchers.append(dict(
        group='recording', name='recording-current-state', label='Current state',
        view_class=CurrentStateView,
        context=recording_context, opts=dict(),
        enabled=(recording_context is not None)
    ))
    if recording_context:
        if recording_context.hasIntraRecording():
            launchers.append(dict(
                group='recording', name='intra-timeseries', label='Intra-timeseries',
                view_class=TimeseriesView,
                context=recording_context, opts=dict(),
                enabled=(recording_context is not None)
            ))

    launchers.append(dict(
        group='unit', name='test', label='Test',
        view_class=TemplatesView,
        context=recording_context, opts=dict(),
        enabled=(recording_context is not None) and (recording_context.currentUnitId() is not None)
    ))
    
    
    return ret
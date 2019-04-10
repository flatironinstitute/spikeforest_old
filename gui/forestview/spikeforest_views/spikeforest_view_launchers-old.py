from .currentstateview import CurrentStateView
from .recordingtableview import RecordingTableView

def get_spikeforest_view_launchers(context):
    return [
        dict(
            name='recording-table',
            label='Recording table',
            view_class=RecordingTableView,
            context=context,
            opts=dict(),
            enabled=True
        ),
        dict(
            name='current-state',
            label='Current state',
            view_class=CurrentStateView,
            context=context,
            opts=dict(),
            enabled=True
        ),
        dict(
            name='test-name',
            label='Testing',
            view_class=CurrentStateView,
            context=context,
            opts=dict(),
            enabled=(context.currentRecordingId() is not None)
        )
    ]


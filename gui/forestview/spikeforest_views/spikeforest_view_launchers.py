from .currentstateview import CurrentStateView
from .recordingtableview import RecordingTableView

def get_spikeforest_view_launchers():
    return [
        dict(
            name='recording-table',
            label='Recording table',
            view_class=RecordingTableView
        ),
        dict(
            name='current-state',
            label='Current state',
            view_class=CurrentStateView
        )
    ]


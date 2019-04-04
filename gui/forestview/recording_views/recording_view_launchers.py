from .recordingsummaryview import RecordingSummaryView
from .timeseriesview import TimeseriesView
from .testplotlyview import TestPlotlyView
from .unitstableview import UnitsTableView
from .templatesview import TemplatesView
from .electrodegeometryview import ElectrodeGeometryView
from .currentstateview import CurrentStateView
from .unitdetailview import UnitDetailView

def get_recording_view_launchers():
    return [
        dict(
            name='recording-summary',
            label='Recording summary',
            view_class=RecordingSummaryView
        ),
        dict(
            name='electrode-geometry',
            label='Electrode geometry',
            view_class=ElectrodeGeometryView
        ),
        dict(
            name='timeseries',
            label='Timeseries',
            view_class=TimeseriesView
        ),
        dict(
            name='templates',
            label='Template plots',
            view_class=TemplatesView
        ),
        dict(
            name='true-units-table',
            label='Units table',
            view_class=UnitsTableView
        ),
        dict(
            name='current-unit-detail',
            label='Current unit detail',
            view_class=UnitDetailView
        ),
        dict(
            name='current-state',
            label='Current state',
            view_class=CurrentStateView
        )
    ]
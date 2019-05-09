from .spikeforest_views.currentstateview import CurrentStateView
from .spikefront_views.mainresulttableview import MainResultTableView

import vdomr as vd
from mountaintools import client as mt
import json


def get_spikefront_view_launchers(context):
    launchers = []
    groups = []
    ret = dict(
        groups=groups,
        launchers=launchers
    )

    # General
    groups.append(dict(name='general', label=''))

    launchers.append(dict(
        group='general', name='current-state', label='Current state',
        view_class=CurrentStateView,
        context=context, opts=dict(),
        enabled=True
    ))

    launchers.append(dict(
        group='general', name='main-result-table', label='Main result table',
        view_class=MainResultTableView,
        context=context, opts=dict(),
        always_open_new=False,
        enabled=True
    ))

    return ret

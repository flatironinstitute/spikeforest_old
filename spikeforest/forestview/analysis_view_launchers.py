from .spikeforest_views.currentstateview import CurrentStateView
from .analysis_views.analysissummaryview import AnalysisSummaryView
from .analysis_views.sorterdefinitionsview import SorterDefinitionsView
from .analysis_views.testview import TestView

import vdomr as vd
from mountaintools import client as mt
import json

def get_analysis_view_launchers(context):
    analysis_context = context

    launchers=[]
    groups=[]
    ret = dict(
        groups=groups,
        launchers=launchers
    )

    # General
    groups.append(dict(name='general',label=''))

    launchers.append(dict(
        group='general', name='analysis-summary', label='Analysis summary',
        view_class=AnalysisSummaryView,
        context=analysis_context, opts=dict(),
        enabled=True
    ))
    launchers.append(dict(
        group='general', name='sorter-definitions', label='Sorter definitions',
        view_class=SorterDefinitionsView,
        context=analysis_context, opts=dict(),
        enabled=True
    ))
    launchers.append(dict(
        group='general', name='test-view', label='Test view',
        view_class=TestView,
        context=analysis_context, opts=dict(),
        enabled=True
    ))
    launchers.append(dict(
        group='general', name='current-state', label='Current state',
        view_class=CurrentStateView,
        context=analysis_context, opts=dict(),
        enabled=True
    ))
    
    return ret

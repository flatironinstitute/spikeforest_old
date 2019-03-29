import mlprocessors as mlpr
from mountaintools import client as mt
import os
from copy import deepcopy
import mtlogging

@mtlogging.log()
def summarize_sortings(sortings,compute_resource,label=None):
    print('')
    print('>>>>>> {}'.format(label or 'summarize sortings'))
    
    print('Gathering summarized sortings...')
    summarized_sortings=[]
    for sorting in sortings:
        summary=dict()
        summary['plots']=dict()

        sorting2=deepcopy(sorting)
        sorting2['summary']=summary
        summarized_sortings.append(sorting2)

    return summarized_sortings

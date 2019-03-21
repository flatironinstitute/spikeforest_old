import functools
import logging
import time
import json
from copy import deepcopy

_global=dict(
    current_node=None
)

def log(*, name=None, root=False):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            last_current_node = _global['current_node']
            if root:
                node=LogNode(function=function, name=name)
            else:
                if last_current_node:
                    node=last_current_node.addChild(function=function, name=name)
                else:
                    node=None
            _global['current_node']=node
            if node:
                node.reportStart()
            try:
                ret = function(*args, **kwargs)
            except:
                if node:
                    node.reportException()
                    node.reportEnd()
                    if root:
                        write_summary(node.getLogObject())
                    _global['current_node'] = last_current_node
                raise
            if node:
                node.reportEnd()
                if root:
                    write_summary(node.getLogObject())
            _global['current_node'] = last_current_node
            return ret
        return wrapper
    return decorator

def aggregate(obj):
    obj2=deepcopy(obj)
    child_names=list(set([ch['name'] for ch in obj['children']]))
    child_names.sort()
    obj2['children']=[]
    nodes_by_chname=dict()
    for chname in child_names:
        node=dict(
            name=chname,
            num_calls=0,
            elapsed_time=0,
            children=[]
        )
        obj2['children'].append(node)
        nodes_by_chname[chname]=node
    for ch in obj['children']:
        x = nodes_by_chname[ch['name']]
        x['num_calls']=x['num_calls']+ch['num_calls']
        x['elapsed_time']=x['elapsed_time']+ch['elapsed_time']
        x['children']=x['children']+ch['children']
    for i,ch in enumerate(obj2['children']):
        obj2['children'][i]=aggregate(ch)
    return obj2

def write_summary(obj, indent=''):
    if indent=='':
        print('')
        print('============================================================================================')
    obj=aggregate(obj)
    print('{}{}: {} calls, {} sec'.format(indent, obj['name'], obj['num_calls'], obj['elapsed_time']))
    children=obj['children']
    children.sort(key=lambda ch: ch['elapsed_time'], reverse=True)
    for ch in children:
        write_summary(ch, indent=indent+'  ')
    if indent=='':
        print('============================================================================================')
        print('')

class LogNode():
    def __init__(self, *, function, parent=None, name=None):
        self._function=function
        self._parent=parent
        self._children=[]
        self._start_time=None
        self._end_time=None
        self._has_exception=False
        self._name = name or function.__name__
    def reportStart(self):
        self._start_time=time.time()
    def reportEnd(self):
        self._end_time=time.time()
    def reportException(self):
        self._has_exception=True
    def parent(self):
        return self._parent
    def addChild(self, function, **kwargs):
        child=LogNode(parent=self, function=function, **kwargs)
        self._children.append(child)
        return child
    def getLogObject(self):
        return dict(
            name=self._name,
            start_time=self._start_time,
            end_time=self._end_time,
            elapsed_time=self._end_time-self._start_time,
            num_calls=1,
            has_exception=self._has_exception,
            children=[ch.getLogObject() for ch in self._children]
        )
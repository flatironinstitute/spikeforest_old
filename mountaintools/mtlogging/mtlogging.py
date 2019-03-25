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
            parent_node = _global['current_node']
            node = LogNode(name=name or function.__name__, is_root=root)
            if parent_node:
                if parent_node.currentSubNode():
                    parent_node.currentSubNode()._add_child_node(node)
                else:
                    parent_node._add_child_node(node)
            _global['current_node']=node
            node.reportStart()
            try:
                ret = function(*args, **kwargs)
            except:
                if node:
                    node.reportException()
                    node.reportEnd()
                    _global['current_node'] = parent_node
                raise
            node.reportEnd()
            _global['current_node'] = parent_node
            return ret
        return wrapper
    return decorator

def sublog(name):
    parent_node = _global['current_node']
    if name is None:
        parent_node.endSubNode()
        return
    subnode = LogNode(name=name, is_root=False)
    parent_node.startSubNode(subnode)

def aggregate(obj):
    obj2 = deepcopy(obj)
    child_labels = list(set([ch['label'] for ch in obj['children']]))
    child_labels.sort()
    obj2['children'] = []
    nodes_by_chlabel = dict()
    for chlabel in child_labels:
        node = dict(
            label=chlabel,
            num_calls=0,
            elapsed_time=0,
            children=[]
        )
        obj2['children'].append(node)
        nodes_by_chlabel[chlabel] = node
    for ch in obj['children']:
        x = nodes_by_chlabel[ch['label']]
        x['num_calls'] = x['num_calls']+ch['num_calls']
        x['elapsed_time'] = x['elapsed_time']+ch['elapsed_time']
        x['children'] = x['children']+ch['children']
    for i,ch in enumerate(obj2['children']):
        obj2['children'][i] = aggregate(ch)
    return obj2

def write_summary(obj, indent=''):
    if indent == '':
        print('')
        print('============================================================================================')
    obj = aggregate(obj)
    print('{}{}: {} calls, {} sec'.format(indent, obj['label'], obj['num_calls'], obj['elapsed_time']))
    children = obj['children']
    children.sort(key=lambda ch: ch['elapsed_time'], reverse=True)
    for ch in children:
        if ch['elapsed_time'] >= 0.01:
            write_summary(ch, indent=indent+'|   ')
    if indent == '':
        print('============================================================================================')
        print('')

class LogNode():
    def __init__(self, *, name, is_root):
        self._children = []
        self._start_time = None
        self._end_time = None
        self._has_exception = False
        self._name = name
        self._is_root = is_root
        self._current_subnode = None
    def label(self):
        if self._has_exception:
            return '*'+self._name
        else:
            return self._name
    def reportStart(self):
        self._start_time = time.time()
    def reportEnd(self):
        if self.currentSubNode():
            self.currentSubNode().reportEnd()
        self._end_time = time.time()
        if self._is_root:
            write_summary(self.getLogObject())
    def reportException(self):
        self._has_exception=True
    def getLogObject(self):
        return dict(
            name=self._name,
            label=self.label(),
            start_time=self._start_time,
            end_time=self._end_time,
            elapsed_time=self._end_time-self._start_time,
            num_calls=1,
            has_exception=self._has_exception,
            children=[ch.getLogObject() for ch in self._children]
        )
    def currentSubNode(self):
        return self._current_subnode
    def startSubNode(self, subnode):
        if self._current_subnode:
            self._current_subnode.reportEnd()
        self._children.append(subnode)
        self._current_subnode=subnode
        subnode.reportStart()
    def endSubNode(self):
        if self._current_subnode:
            self._current_subnode.reportEnd()
            self._current_subnode = None
    def _add_child_node(self, child_node):
        self._children.append(child_node)
import os
import vdomr as vd
from mountaintools import client as mt
from batchmonitor import BatchMonitor


class ResourceSelectWidget(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)

        self._SEL_resource_name = vd.components.SelectBox(options=[])
        self._SEL_resource_name.onChange(self._on_resource_name_changed)
        self._selection_changed_handlers = []

        vd.devel.loadBootstrap()

    def initialize(self):
        #self._resource_names = ca.getSubKeys(key=dict(name='spikeforest_results'))
        obj = mt.getValue(key=dict(name='compute_resources'), subkey='-', parse_json=True)
        if obj:
            self._resource_names =  list(obj.keys())
        else:
            self._resource_names = ['none-found']
        self._SEL_resource_name.setOptions(['']+self._resource_names)
        self._on_resource_name_changed(value=self._SEL_resource_name.value())

    def onSelectionChanged(self, handler):
        self._selection_changed_handlers.append(handler)

    def resourceName(self):
        return self._SEL_resource_name.value()

    def _on_resource_name_changed(self, value):
        for handler in self._selection_changed_handlers:
            handler()

    def render(self):
        rows = [
            vd.tr(vd.td('Select a resource name:'), vd.td(self._SEL_resource_name)),
        ]
        select_table = vd.table(
            rows, style={'text-align': 'left', 'width': 'auto'}, class_='table')
        return vd.div(
            select_table
        )


class BatchMonitorMainWindow(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._resource_select_widget = ResourceSelectWidget()
        self._batch_monitor = None

        self._resource_select_widget.onSelectionChanged(
            self._on_selection_changed)
        self._resource_select_widget.initialize()

    def _on_selection_changed(self):
        resource_name = self._resource_select_widget.resourceName()
        if not resource_name:
            return
        self._batch_monitor = BatchMonitor(resource_name=resource_name)
        self.refresh()

    def render(self):
        list = [self._resource_select_widget]
        if self._batch_monitor:
            list.append(self._batch_monitor)
        return vd.div(
            list
        )

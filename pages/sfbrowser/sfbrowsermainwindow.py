import os
import vdomr as vd
import spikeforest as sf
from kbucket import client as kb
import spikeforestwidgets as SFW
from .sfbrowser import SFBrowser


class GroupSelectWidget(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)

        self._SEL_group = vd.components.SelectBox(options=[])
        self._SEL_group.onChange(self._on_group_changed)
        self._selection_changed_handlers = []

        vd.devel.loadBootstrap()

    def initialize(self):
        self._groups = kb.loadObject(
            key=dict(name='spikeforest_batch_group_names'))
        self._SEL_group.setOptions(['']+self._groups['batch_group_names'])
        self._SEL_group.setValue('magland_synth')
        self._on_group_changed(value=self._SEL_group.value())

    def onSelectionChanged(self, handler):
        self._selection_changed_handlers.append(handler)

    def group(self):
        return self._SEL_group.value()

    def _on_group_changed(self, value):
        for handler in self._selection_changed_handlers:
            handler()

    def render(self):
        rows = [
            vd.tr(vd.td('Select a group:'), vd.td(self._SEL_group)),
        ]
        select_table = vd.table(
            rows, style={'text-align': 'left', 'width': 'auto'}, class_='table')
        return vd.div(
            select_table
        )


class SFBrowserMainWindow(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._group_select_widget = GroupSelectWidget()
        self._sf_browser = None

        self._group_select_widget.onSelectionChanged(
            self._on_selection_changed)
        self._group_select_widget.initialize()

    def _on_selection_changed(self):
        group = self._group_select_widget.group()
        if not group:
            return
        self._sf_browser = SFBrowser(group=group)
        self.refresh()

    def render(self):
        list = [self._group_select_widget]
        if self._sf_browser:
            list.append(self._sf_browser)
        return vd.div(
            list
        )

import os
import vdomr as vd
import spikeforest as sf
from cairio import client as ca
import spikeforestwidgets as SFW
from sfbrowser import SFBrowser


class OutputIdSelectWidget(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)

        self._SEL_output_id = vd.components.SelectBox(options=[])
        self._SEL_output_id.onChange(self._on_output_id_changed)
        self._selection_changed_handlers = []

        vd.devel.loadBootstrap()

    def initialize(self):
        self._output_ids = ca.getSubKeys(key=dict(name='spikeforest_results'))
        self._SEL_output_id.setOptions(['']+self._output_ids)
        self._on_output_id_changed(value=self._SEL_output_id.value())

    def onSelectionChanged(self, handler):
        self._selection_changed_handlers.append(handler)

    def outputId(self):
        return self._SEL_output_id.value()

    def _on_output_id_changed(self, value):
        for handler in self._selection_changed_handlers:
            handler()

    def render(self):
        rows = [
            vd.tr(vd.td('Select an output ID:'), vd.td(self._SEL_output_id)),
        ]
        select_table = vd.table(
            rows, style={'text-align': 'left', 'width': 'auto'}, class_='table')
        return vd.div(
            select_table
        )


class SFBrowserMainWindow(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._output_id_select_widget = OutputIdSelectWidget()
        self._sf_browser = None

        self._output_id_select_widget.onSelectionChanged(
            self._on_selection_changed)
        self._output_id_select_widget.initialize()

    def _on_selection_changed(self):
        output_id = self._output_id_select_widget.outputId()
        if not output_id:
            return
        self._sf_browser = SFBrowser(output_id=output_id)
        self.refresh()

    def render(self):
        list = [self._output_id_select_widget]
        if self._sf_browser:
            list.append(self._sf_browser)
        return vd.div(
            list
        )

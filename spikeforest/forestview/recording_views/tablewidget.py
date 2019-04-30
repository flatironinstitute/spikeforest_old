import vdomr as vd
import os

source_path=os.path.dirname(os.path.realpath(__file__))
class TableWidget(vd.Component):
    def __init__(self, *, columns, records, height=None):
        vd.Component.__init__(self)
        self._columns = columns
        self._records = records
        self._height = height
        self._current_row_index = None
        self._selection_changed_handlers = []
        vd.devel.loadBootstrap()
        vd.devel.loadJavascript(path=source_path+'/tablewidget.js')
        vd.devel.loadJavascript(path=source_path+'/../../spikeforestwidgets/dist/jquery-3.3.1.min.js')
        vd.devel.loadCss(css=_CSS)
    def currentRowIndex(self):
        return self._current_row_index
    def setCurrentRowIndex(self, index):
        if self._current_row_index == index:
            return
        self._current_row_index = index
        js = """
        let W = window.widgets['{component_id}'];
        if (W) {
            W.setCurrentRowIndex({current_row_index});
        }
        """
        js = js.replace('{component_id}', self.componentId())
        
        if self._current_row_index is None:
            js = js.replace('{current_row_index}', 'null')
        else:
            js = js.replace('{current_row_index}', str(self._current_row_index))

        self.executeJavascript(js=js)
    def onSelectionChanged(self, handler):
        self._selection_changed_handlers.append(handler)
    def render(self):
        rows = []
        rows.append(vd.tr(
            *[vd.th(c['label']) for c in self._columns]
        ))
        for index, record in enumerate(self._records):
            rows.append(vd.tr(
                *[vd.td(record.get(c['name'], '')) for c in self._columns],
                class_ = 'tablewidget_row', id='{}'.format(index)
            ))
        table = vd.table(*rows, class_='table tablewidget', id='table-'+self.componentId())
        if self._height:
             return vd.div(ScrollArea(table, height=self._height))
        else:
            return table
    def _on_selection_changed(self, current_id, selected_ids):
        if type(current_id)==str:
            current_id=int(current_id)
        self._current_row_index = current_id
        for handler in self._selection_changed_handlers:
            handler()

    def postRenderScript(self):
        js="""
        let W = new window.TableWidget($('#table-{component_id}'));
        W.onSelectionChanged(function(current_id, selected_ids) {
            {on_selection_changed}([current_id, selected_ids], {})
        });
        W.setCurrentRowIndex({current_row_index});
        window.widgets=window.widgets||{};
        window.widgets['{component_id}']=W;
        """
        js = js.replace('{component_id}', self.componentId())
        js = js.replace('{on_selection_changed}', vd.create_callback(self._on_selection_changed))

        if self._current_row_index is None:
            js = js.replace('{current_row_index}', 'null')
        else:
            js = js.replace('{current_row_index}', str(self._current_row_index))

        return js

_CSS = """
.tablewidget tr:hover td {
  background-color:rgb(240,240,240);
}
.tablewidget tr.selected td {
  background-color:rgb(240,240,200);
}
.tablewidget tr.current td {
  background-color:rgb(240,240,180);
}
"""

class ScrollArea(vd.Component):
    def __init__(self, child, *, height):
        vd.Component.__init__(self)
        self._child = child
        self._height = height

    def render(self):
        return vd.div(self._child, style=dict(overflow='auto', height='{}px'.format(self._height)))
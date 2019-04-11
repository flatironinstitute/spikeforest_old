import vdomr as vd
import time
import sys
import mtlogging
from mountaintools import client as mt
from .tablewidget import TableWidget

class SortingResultsTableView(vd.Component):
    def __init__(self, context, opts=None):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        self._table_widget = SortingResultsTableWidget(
            context=self._context
        )
        self._table_widget.setSize(self._size)
    def setSize(self, size):
        self._size=size
        if self._table_widget:
            self._table_widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Sorting results table'
    def render(self):
        return self._table_widget

class SortingResultsTableWidget(vd.Component):
    def __init__(self, *, context):
        vd.Component.__init__(self)
        self._context = context
        self._size = (100,100)
        self._sorting_result_names = self._context.sortingResultNames()
        self._context.onCurrentSortingResultChanged(self._on_context_selection_changed)
        self._update_table()
    def setSize(self, size):
        self._size = size
        self._update_table()
    def _update_table(self):
        self._table_widget = TableWidget(
            columns = [
                dict(label='Sorting result', name='sorting_result_name')
            ],
            records = [dict(sorting_result_name=srname) for srname in self._sorting_result_names],
            height=self._size[1]
        )
        self._table_widget.onSelectionChanged(self._on_widget_selection_changed)
        self._on_context_selection_changed()
        self.refresh()
    def _on_widget_selection_changed(self):
        current_row_index = self._table_widget.currentRowIndex()
        if current_row_index is not None:
            self._context.setCurrentSortingResult(self._sorting_result_names[current_row_index])
        else:
            self._context.setCurrentSortingResult(None)
    def _on_context_selection_changed(self):
        srname = self._context.currentSortingResult()
        if srname is not None:
            try:
                index0 = self._sorting_result_names.index(srname)
            except:
                index0 = None
        else:
            index0 = None
        self._table_widget.setCurrentRowIndex(index0)
    def render(self):
        return self._table_widget
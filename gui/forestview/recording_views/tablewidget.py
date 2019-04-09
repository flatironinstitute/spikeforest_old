import vdomr as vd

class TableWidget(vd.Component):
    def __init__(self, *, columns, records, height=None):
        vd.Component.__init__(self)
        self._columns = columns
        self._records = records
        self._height = height
        vd.devel.loadBootstrap()
    def render(self):
        rows = []
        rows.append(vd.tr(
            *[vd.th(c['label']) for c in self._columns]
        ))
        for record in self._records:
            rows.append(vd.tr(
                *[vd.td(record.get(c['name'], '')) for c in self._columns]
            ))
        table = vd.table(*rows, class_='table')
        if self._height:
             return vd.div(ScrollArea(table, height=self._height))
        else:
            return table

class ScrollArea(vd.Component):
    def __init__(self, child, *, height):
        vd.Component.__init__(self)
        self._child = child
        self._height = height

    def render(self):
        return vd.div(self._child, style=dict(overflow='auto', height='{}px'.format(self._height)))
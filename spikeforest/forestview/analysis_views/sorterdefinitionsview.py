import vdomr as vd
import json

class SorterDefinitionsView(vd.Component):
    def __init__(self, context, opts=None):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
    def setSize(self, size):
        self._size = size
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Sorter definitions'
    def render(self):
        # row info for the table
        rr = []
        sdkeys = self._context.sorterDefinitionKeys()
        for sdkey in sdkeys:
            sdef = self._context.sorterDefinition(sdkey)
            rr.append(dict(label=sdkey, value=vd.pre(json.dumps(sdef, indent=4))))

        rows = []
        for r in rr:
            rows.append(vd.tr(
                vd.th(r['label']), vd.td(r['value'])
            ))

        table = vd.table(rows, style={
                         'text-align': 'left', 'width': 'auto', 'font-size': '13px'}, class_='table')

        return vd.components.ScrollArea(vd.div(
            vd.h2('Sorter definitions for analysis: {}'.format(self._context.analysisName())),
            table, height=self._size[1]
        ))
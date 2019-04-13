import vdomr as vd

class AnalysisSummaryView(vd.Component):
    def __init__(self, context, opts=None, prepare_result=None):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
    @staticmethod
    def prepareView(context, opts):
        context.initialize()
    def setSize(self, size):
        self._size = size
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Analysis summary'
    def render(self):
        # row info for the table
        rr = []
        rr.append(dict(label='Recording groups', value=', '.join(self._context.recordingGroups())))
        rr.append(dict(label='Sorters to run', value=', '.join(self._context.sorterKeys())))
        rr.append(dict(label='Output path', value=self._context.outputPath()))
        rr.append(dict(label='Download from', value=', '.join(self._context.downloadFrom())))
        rr.append(dict(label='Job timeout (sec)', value=self._context.jobTimeout()))
        rr.append(dict(label='Compute resources', value=', '.join(self._context.computeResourceKeys())))
        rr.append(dict(label='Sorter definition keys', value=', '.join(self._context.sorterDefinitionKeys())))

        rows = []
        for r in rr:
            rows.append(vd.tr(
                vd.th(r['label']), vd.td(r['value'])
            ))

        table = vd.table(rows, style={
                         'text-align': 'left', 'width': 'auto', 'font-size': '13px'}, class_='table')

        return vd.components.ScrollArea(vd.div(
            vd.h2('Analysis: {}'.format(self._context.analysisName())),
            table, height=self._size[1]
        ))
import vdomr as vd

class RecordingSummaryView(vd.Component):
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
        return 'Recording summary'
    def render(self):
        rows = []
        rows.append(vd.tr(
            vd.th('Study'), vd.td(self._context.studyName())
        ))
        rows.append(vd.tr(
            vd.th('Recording'), vd.td(self._context.recordingName())
        ))
        rows.append(vd.tr(
            vd.th('Directory'), vd.td(self._context.recordingDirectory())
        ))
        RX = self._context.recordingExtractor()
        rows.append(vd.tr(
            vd.th('Num. channels'), vd.td('{}'.format(len(RX.getChannelIds())))
        ))
        rows.append(vd.tr(
            vd.th('Samplerate'), vd.td('{}'.format(RX.getSamplingFrequency()))
        ))
        a = RX.getNumFrames() / RX.getSamplingFrequency()
        rows.append(vd.tr(            
            vd.th('Duration (s)'), vd.td('{}'.format(a))
        ))

        a = ', '.join(self._context.sortingResultNames())
        rows.append(vd.tr(            
            vd.th('Sorting results'), vd.td('{}'.format(a))
        ))

        sc_true = self._context.trueSortingContext()
        if sc_true:
            SX_true = sc_true.sortingExtractor()
            true_unit_ids = SX_true.getUnitIds()
            rows.append(vd.tr(
                vd.th('Num. true units'), vd.td('{}'.format(len(true_unit_ids)))
            ))

        table = vd.table(rows, style={
                         'text-align': 'left', 'width': 'auto', 'font-size': '13px'}, class_='table')

        return vd.div(
            vd.h2('{}/{}'.format(self._context.studyName(), self._context.recordingName())),
            table
        )
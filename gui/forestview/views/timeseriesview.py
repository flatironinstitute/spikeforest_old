import vdomr as vd
import spikeforestwidgets as SFW
import spikeextractors as se
import time

class TimeseriesView(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._size=(100, 100)
        rx = self._context.recordingExtractor()
        # rx = se.SubRecordingExtractor(parent_recording=rx, start_frame=0, end_frame=int(rx.getSamplingFrequency()*1))
        self._timeseries_widget = SFW.TimeseriesWidget(recording=rx)
    def setSize(self, size):
        self._timeseries_widget.setSize(size)
    def size(self):
        return self._timeseries_widget.size()
    def tabLabel(self):
        return 'Timeseries'
    def render(self):
        return vd.div(
            self._timeseries_widget
        )
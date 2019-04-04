import vdomr as vd
import time
import sys
import uuid
import json
import os

source_path=os.path.dirname(os.path.realpath(__file__))

class ElectrodeGeometryView(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._size=None
        self._widget = ElectrodeGeometryWidget(recording=context.recordingExtractor())
        self.setSize((100,100))
    def setSize(self, size):
        if self._size == size:
            return
        self._size = size
        self._widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Electrode geometry'
    def render(self):
        return vd.div(self._widget)

class ElectrodeGeometryWidget(vd.Component):
    def __init__(self, recording):
        vd.Component.__init__(self)
        self._recording = recording
        self._div_id = 'electrode-geometry-' + str(uuid.uuid4())
        self._size=(200,200)

        vd.devel.loadJavascript(path=source_path+'/../../../spikeforest/spikeforestwidgets/templatewidget/canvaswidget.js')
        vd.devel.loadJavascript(path=source_path+'/electrodegeometrywidget.js')
        vd.devel.loadJavascript(path=source_path+'/../../../spikeforest/spikeforestwidgets/dist/jquery-3.3.1.min.js')

    def setSize(self, size):
        if self._size == size:
            return
        self._size = size
        self.refresh()
    def render(self):
        div=vd.div(id=self._div_id)
        return div
    def postRenderScript(self):
        channel_ids = self._recording.getChannelIds()
        locations = self._recording.getChannelLocations(channel_ids = channel_ids)
        locations = [[loc[0], loc[1]] for loc in locations]
        js="""
        let W=new window.ElectrodeGeometryWidget();
        W.setElectrodeLocations({locations})
        W.setSize({width},{height});
        let elmt=$('#{div_id}');
        if (!elmt) {
            console.error('Error getting element in ElectrodeGeometryWidget');
            return;
        }
        elmt.empty();
        elmt.css({width:'{width}px',height:'{height}px'})
        elmt.append(W.element());
        """
        js = js.replace('{div_id}', self._div_id)
        js = js.replace('{width}', str(self._size[0]))
        js = js.replace('{height}', str(self._size[1]))
        js = js.replace('{locations}', json.dumps(locations))
        return js
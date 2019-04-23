import vdomr as vd
import time
import sys
import uuid
import json
import os
import uuid

source_path=os.path.dirname(os.path.realpath(__file__))

class ElectrodeGeometryView(vd.Component):
    def __init__(self, context, opts=None, prepare_result=None):
        vd.Component.__init__(self)
        self._context = context
        self._size=None
        self._widget = ElectrodeGeometryWidget(recording=context.recordingExtractor())
        self.setSize((100,100))
        self._update_state()
        self._widget.onStateChanged(self._handle_state_changed)
        self._context.onCurrentChannelChanged(self._update_state)
    @staticmethod
    def prepareView(context, opts):
        context.initialize()
    def setSize(self, size):
        if self._size == size:
            return
        self._size = size
        self._widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Electrode geometry'
    def title(self):
        return 'Electrode geometry for {}'.format(self._context.recordingLabel())
    def render(self):
        return vd.div(self._widget)
    def _handle_state_changed(self):
        self._context.setCurrentChannel(self._widget.currentChannel())
    def _update_state(self):
        self._widget.setCurrentChannel(self._context.currentChannel())

class ElectrodeGeometryWidget(vd.Component):
    def __init__(self, recording):
        vd.Component.__init__(self)
        self._recording = recording
        self._div_id = 'electrode-geometry-' + str(uuid.uuid4())
        self._size=(200,200)
        self._current_channel=None
        self._state_changed_handlers=[]

        # HIGH TODO clean up these rel .js reference paths throughout
        vd.devel.loadJavascript(path=source_path+'/../../spikeforestwidgets/templatewidget/canvaswidget.js')
        vd.devel.loadJavascript(path=source_path+'/electrodegeometrywidget.js')
        vd.devel.loadJavascript(path=source_path+'/../..//spikeforestwidgets/dist/jquery-3.3.1.min.js')

    def setSize(self, size):
        if self._size == size:
            return
        self._size = size
        self._update_widget()
    def currentChannel(self):
        return self._current_channel
    def setCurrentChannel(self, ch):
        if self._current_channel == ch:
            return
        self._current_channel = ch
        self._update_widget()
        for handler in self._state_changed_handlers:
            handler()
    def onStateChanged(self, handler):
        self._state_changed_handlers.append(handler)
    def _on_state_change(self, current_electrode_index):
        current_electrode_index=int(current_electrode_index)
        channel_ids = self._recording.getChannelIds()
        if current_electrode_index>=0:
            ch = channel_ids[int(current_electrode_index)]
        else:
            ch=None
        self.setCurrentChannel(ch)
    def _update_widget(self):
        channel_ids = self._recording.getChannelIds()
        locations = self._recording.getChannelLocations(channel_ids = channel_ids)
        locations = [[loc[0], loc[1]] for loc in locations]
        try:
            current_electrode_index = channel_ids.index(self._current_channel)
        except:
            current_electrode_index = -1

        js = """
        let W = (window.geom_widgets||{})['{component_id}'];
        W.setSize({width},{height});
        W.setElectrodeLocations({locations});
        W.setElectrodeLabels({labels});
        W.setCurrentElectrodeIndex({current_electrode_index});

        let elmt = $('#{div_id}');
        elmt.css({width:'{width}px',height:'{height}px'})
        """
        js = js.replace('{div_id}', self._div_id)
        js = js.replace('{component_id}', self.componentId())
        js = js.replace('{locations}', json.dumps(locations))
        js = js.replace('{labels}', json.dumps([ch for ch in channel_ids]))
        js = js.replace('{current_electrode_index}', str(current_electrode_index))
        js = js.replace('{width}', str(self._size[0]))
        js = js.replace('{height}', str(self._size[1]))
        self.executeJavascript(js)
    def render(self):
        div=vd.div(id=self._div_id)
        return div
    def postRenderScript(self):
        state_change_callback_id = 'state-change-callback-' + str(uuid.uuid4())
        vd.register_callback(state_change_callback_id, lambda current_electrode_index: self._on_state_change(current_electrode_index=current_electrode_index))

        js="""
        let W=new window.ElectrodeGeometryWidget();
        if (!window.geom_widgets) window.geom_widgets={};
        window.geom_widgets['{component_id}']=W;
        W.onCurrentElectrodeIndexChanged(function() {
            window.vdomr_invokeFunction('{state_change_callback_id}', [Number(W.currentElectrodeIndex())], {})
        });
        let elmt = $('#{div_id}');
        elmt.append(W.element());
        """
        js = js.replace('{div_id}', self._div_id)
        js = js.replace('{component_id}', self.componentId())
        
        js = js.replace('{state_change_callback_id}', str(state_change_callback_id))
        self._update_widget()
        return js
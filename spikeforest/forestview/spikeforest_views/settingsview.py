import vdomr as vd
import json

class SettingsView(vd.Component):
    def __init__(self, context, opts=None):
        vd.Component.__init__(self)
        self._context = context
        self._context.onAnyStateChanged(self.refresh)
        self._size=(100,100)

        try: 
            recid = self._context.currentRecordingId()
            self.recording_context = self._context._recording_contexts[recid]
            self.recording_context.onAnyStateChanged(self.refresh)

            self._select_box = vd.components.SelectBox(style={'width':'100%', 'font-size':'12px'})
            self._select_box.onChange(self._on_selection_changed)
            #self._on_selection_changed('True')
            self._select_box.setOptions(['false', 'true'])
            self._select_box.setValue(str(self.recording_context._state['bandpass_filter']))
        except:
            None

    def _on_selection_changed(self, value):
        self.recording_context._state['bandpass_filter'] = bool(self._select_box.index())
        self.recording_context._init_recording()
        self.refresh()

    def tabLabel(self):
        return 'Settings'

    def setSize(self, size):
        if self._size == size:
            return
        self._size = size
        self.refresh()
    def size(self):
        return self._size
    def render(self):
        state0 = self._context.stateObject()
        try:
            options = vd.div(
                    vd.h2('Timeseries'),
                    vd.label('Bandpass Filter:'),
                    self._select_box
                    )
        except:
            options = vd.div()

        return vd.div(
                vd.pre(
                    json.dumps(state0, indent=4)
                    ),
                options
                )

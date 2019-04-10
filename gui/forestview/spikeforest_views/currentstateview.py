import vdomr as vd
import json

class CurrentStateView(vd.Component):
    def __init__(self, context, opts=None):
        vd.Component.__init__(self)
        self._context = context
        self._context.onAnyStateChanged(self.refresh)
        self._size=(100,100)
    def tabLabel(self):
        return 'Current state'
    def setSize(self, size):
        if self._size == size:
            return
        self._size = size
        self.refresh()
    def size(self):
        return self._size
    def render(self):
        state0 = self._context.stateObject()
        return vd.div(
            vd.pre(
                json.dumps(state0, indent=4)
            )
        )
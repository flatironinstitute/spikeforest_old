import vdomr as vd

class ForestViewControlPanel(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context

        self._view_launchers = dict()
        self._launch_view_handlers = []

    def addViewLauncher(self, name, view_launcher):
        self._view_launchers[name] = view_launcher

    def onLaunchView(self, handler):
        self._launch_view_handlers.append(handler)

    def render(self):
        view_launcher_buttons = []
        for name, VL in self._view_launchers.items():
            button0 = vd.components.Button(label=VL['label'], onclick=lambda VL=VL: self._trigger_launch_view(VL))
            view_launcher_buttons.append(button0)

        return vd.div(
            *view_launcher_buttons
        )

    def _trigger_launch_view(self, VL):
        for handler in self._launch_view_handlers:
            handler(VL)
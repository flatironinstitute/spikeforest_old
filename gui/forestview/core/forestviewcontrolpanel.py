import vdomr as vd

class ForestViewControlPanel(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context

        self._view_launchers = dict()
        self._launch_view_handlers = []

    def addViewLauncher(self, view_launcher):
        self._view_launchers[view_launcher['name']] = view_launcher

    def onLaunchView(self, handler):
        self._launch_view_handlers.append(handler)

    def render(self):
        view_launcher_buttons = []
        for _, VL in self._view_launchers.items():
            button0 = vd.components.Button(label=VL['label'], onclick=lambda VL=VL: self._trigger_launch_view(VL), style=dict(width='130px', height='80px', margin='5px'))
            view_launcher_buttons.append(button0)

        table = _make_button_table(view_launcher_buttons, num_columns=2)
        return vd.div(
            table
        )

    def _trigger_launch_view(self, VL):
        for handler in self._launch_view_handlers:
            handler(VL)

def _make_button_table(buttons, num_columns):
    rows = []
    i = 0
    while i<len(buttons):
        row_buttons = buttons[i:i+num_columns]
        while len(row_buttons)<num_columns:
            row_buttons.append(vd.span())
        rows.append(vd.tr([
            vd.td(button)
            for button in row_buttons
        ]))
        i = i+num_columns
    return vd.table(*rows)
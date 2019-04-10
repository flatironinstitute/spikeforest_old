import vdomr as vd

class ForestViewControlPanel(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context

        self._launch_view_handlers = []
        self._context.onAnyStateChanged(self.refresh)

    def onLaunchView(self, handler):
        self._launch_view_handlers.append(handler)

    def render(self):
        view_launchers = self._context.viewLaunchers()
        groups = view_launchers['groups']
        elements = []
        for group in groups:
            view_launcher_buttons = []
            for VL in view_launchers['launchers']:
                if VL['group'] == group['name']:
                    attrs=dict()
                    style0=dict(width='130px', height='80px', margin='5px')
                    if not VL['enabled']:
                        attrs['disabled'] = 'disabled'
                        style0['color'] = 'lightgray'
                    button0 = vd.components.Button(
                        label=VL['label'],
                        onclick=lambda VL=VL: self._trigger_launch_view(VL),
                        style=style0,
                        **attrs
                    )
                    view_launcher_buttons.append(button0)
            table = _make_button_table(view_launcher_buttons, num_columns=2)
            if group['label'] is not '':
                elements.append(vd.h3(group['label']))
            elements.append(table)

        return vd.div(
            *elements
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
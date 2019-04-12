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
            view_launcher_components = []
            group_elements = []
            for VL in view_launchers['launchers']:
                if VL['group'] == group['name']:
                    attrs=dict()
                    style0={'width':'130px', 'height':'28px', 'margin':'5px', 'font-size':'10px'}
                    if not VL['enabled']:
                        attrs['disabled'] = 'disabled'
                        style0['color'] = 'lightgray'
                    if 'view_class' in VL:
                        button0 = vd.components.Button(
                            label=VL['label'],
                            onclick=lambda VL=VL: self._trigger_launch_view(VL),
                            style=style0,
                            **attrs
                        )
                        view_launcher_buttons.append(button0)
                    elif 'component_class' in VL:
                        component = VL['component_class'](context=VL['context'], opts=VL['opts'])
                        view_launcher_components.append(component)
                    else:
                        print(VL)
                        raise Exception('Problem with view launcher.')
            table = _make_button_table(view_launcher_buttons, num_columns=2)
            if group['label'] is not '':
                group_elements.append(vd.h4(group['label']))
            if 'sublabel' in group:
                group_elements.append(vd.span(group['sublabel'], style={'overflow-wrap':'break-word','font-size':'11px'}))
            group_elements.append(table)
            for component in view_launcher_components:
                group_elements.append(component)
            elements.append(vd.div(group_elements, style={'border':'solid 2px lightgray', 'padding':'5px', 'margin':'5px'}))

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
    return vd.div(vd.table(*rows), style={'background-color':'lightgray'})
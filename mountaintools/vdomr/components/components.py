import vdomr as vd
from abc import ABC, abstractmethod
import os
import uuid
import json

class SelectBox(vd.Component):
    def __init__(self, options=[], **kwargs):
        vd.Component.__init__(self)
        self._on_change_handlers = []
        self._value = None
        self._kwargs = kwargs
        self.setOptions(options)

    def setOptions(self, options):
        self._options = options
        if self._value not in options:
            self._value = options[0] if options else None
        self.refresh()

    def value(self):
        return self._value

    def index(self):
        return self._options.index(self._value)

    def setValue(self, value):
        self._value = value
        self.refresh()

    def onChange(self, handler):
        self._on_change_handlers.append(handler)

    def _on_change(self, value):
        self._value = value
        for handler in self._on_change_handlers:
            handler(value=value)

    def render(self):
        opts = []
        for option in self._options:
            if option == self._value:
                opts.append(vd.option(option, selected='selected'))
            else:
                opts.append(vd.option(option))
        X = vd.select(opts, onchange=self._on_change, **self._kwargs)
        return X

class RadioButton(vd.Component):
    def __init__(self, checked=False, **kwargs):
        vd.Component.__init__(self)
        self._on_change_handlers = []
        self._checked = checked
        self._kwargs = kwargs

    def setChecked(self, val):
        self._checked = val
        self.refresh()

    def checked(self):
        return self._checked

    def onChange(self, handler):
        self._on_change_handlers.append(handler)

    def _on_click(self):
        self._checked = True
        for handler in self._on_change_handlers:
            handler()

    def render(self):
        kwargs = dict()
        if self._checked:
            kwargs['checked'] = 'checked'
        X = vd.input(type='radio', onclick=self._on_click, **self._kwargs, **kwargs)
        return X


class Button(vd.Component):
    def __init__(self, label, onclick=None, **kwargs):
        vd.Component.__init__(self)
        self._label = label
        self._on_click_handlers = []
        self._kwargs = kwargs
        if onclick:
            self.onClick(onclick)

    def onClick(self, handler):
        self._on_click_handlers.append(handler)

    def label(self):
        return self._label

    def setLabel(self, label):
        self._label = label
        self.refresh()

    def _on_click(self):
        for handler in self._on_click_handlers:
            handler()

    def render(self):
        button = vd.button(self._label, onclick=self._on_click, **self._kwargs)
        return button


class LineEdit(vd.Component):
    def __init__(self, value='', dtype=str, **kwargs):
        vd.Component.__init__(self)
        self._kwargs = kwargs
        self._value = None
        self._dtype = dtype
        if value:
            self.setValue(value)

    def value(self):
        if self._dtype == str:
            return self._value
        else:
            return self._dtype(self._value)

    def setValue(self, value):
        self._value = str(value)
        self.refresh()

    def _on_change(self, value):
        self._value = value

    def render(self):
        X = vd.input(type='text', value=self._value,
                     onchange=self._on_change, **self._kwargs)
        return X


class Pyplot(vd.Component):
    def __init__(self, size=None):
        vd.Component.__init__(self)
        self._size = size
        if self._size is None:
            self._size = (200, 200)
        self._image_data_b64 = None

    @abstractmethod
    def plot(self):
        pass

    def setSize(self, size):
        self._size = size
        self._update_image()

    def _update_image(self):
        self._image_data_b64 = None
        self.refresh()

    def size(self):
        return self._size

    def update(self):
        self._update_image()

    def render(self):
        if self._image_data_b64 is None:
            import base64
            from matplotlib import pyplot as plt
            fig = plt.figure(
                figsize=(self._size[0]/100, self._size[1]/100), dpi=100)
            try:
                self.plot()
            except Exception as e:
                return vd.div('Error in plot: '+str(e))
            tmp_fname = 'tmp_pyplot.jpg'
            _save_plot(fig, tmp_fname, quality=100)
            with open(tmp_fname, 'rb') as f:
                self._image_data_b64 = base64.b64encode(
                    f.read()).decode('utf-8')
            os.remove(tmp_fname)
        src = 'data:image/jpeg;base64, {}'.format(self._image_data_b64)
        elmt = vd.img(src=src)
        return elmt

class PlotlyPlot(vd.Component):
    def __init__(self, data, layout=dict(), config=dict(), size=None):
        vd.Component.__init__(self)
        self._elmt_id = 'PlotlyPlot-'+str(uuid.uuid4())
        self._data = data
        self._layout = layout
        self._config = config
        self._size = size
        vd.devel.loadJavascript(url='https://cdn.plot.ly/plotly-latest.min.js')

    def _filter_data(self, data):
        # mostly to handle numpy arrays
        import numpy as np
        if type(data)==list:
            ret = []
            for val in data:
                ret.append(self._filter_data(val))
            return ret
        elif type(data)==dict:
            ret = dict()
            for key, val in data.items():
                ret[key]=self._filter_data(val)
            return ret
        elif type(data) == np.ndarray:
            if data.ndim != 1:
                raise Exception('At the moment, we only support 1-d numpy arrays.')
            return data.tolist()
        else:
            if _is_jsonable(data):
                return data
            else:
                raise Exception('Unable to JSON serialize data of type {}'.format(str(type(data))))

    def updateSize(self, size):
        if self._size == size:
            return
        self._size = size
        js = """
            function on_plotly_ready(cb) {
                if (window.Plotly) {
                    cb();
                    return;
                }
                setTimeout(function() {
                    on_plotly_ready(cb);
                },100);
            }
            on_plotly_ready(function() { // wait until plotly has loaded
                let div=document.getElementById('{elmt_id}');                
                if (({width}) && ({height}) && (div)) {
                    Plotly.relayout(div, {width:{width}, height:{height}})
                }
            })
        """
        js = js.replace('{elmt_id}', self._elmt_id)
        if self._size:
            width0 = self._size[0]
            height0 = self._size[1]
        else:
            width0 = 'null'
            height0 = 'null'
        js = js.replace('{width}', str(width0))
        js = js.replace('{height}', str(height0))
        self.executeJavascript(js)

    def javascriptPlotObject(self):
        ret = "((window.plotly_plots||{})['{component_id}'])"
        ret = ret.replace('{component_id}', self.componentId())
        return ret

    def render(self):
        div = vd.div('Loading plot...', id=self._elmt_id)
        return div

    # MEDIUM TODO make on_plot_ready more robust... report error after x tries
    def postRenderScript(self):
        data = self._filter_data(self._data)
        if type(data)!=list:
            data=[data]
        if self._size:
            self._layout['width']=self._size[0]
            self._layout['height']=self._size[1]
        js = """
        function on_plotly_ready(cb) {
            if (window.Plotly) {
                cb();
                return;
            }
            setTimeout(function() {
                on_plotly_ready(cb);
            },100);
        }
        on_plotly_ready(function() { // wait until plotly has loaded
            let div=document.getElementById('{elmt_id}');
            div.textContent='';
            if (({width}) && ({height}) && (div)) {
                // div.style="width:{width}px; height:{height}px";
                window.plotly_plots=window.plotly_plots||{};
                Plotly.newPlot(div, {data}, {layout}, {config});
                window.plotly_plots['{component_id}']=div;
            }
        });
        """
        js = js.replace('{elmt_id}', self._elmt_id)
        js = js.replace('{data}', json.dumps(data))
        js = js.replace('{layout}', json.dumps(self._layout or {}))
        js = js.replace('{config}', json.dumps(self._config or {}))
        js = js.replace('{component_id}', self.componentId())
        if self._size:
            width0 = self._size[0]
            height0 = self._size[1]
        else:
            width0 = 'null'
            height0 = 'null'
        js = js.replace('{width}', str(width0))
        js = js.replace('{height}', str(height0))
        return js


class ScrollArea(vd.Component):
    def __init__(self, child, *, width=None, height=None):
        vd.Component.__init__(self)
        self._child = child
        self._width = width
        self._height = height

    def render(self):
        style = dict(overflow='auto', position='absolute')
        if self._width:
            style['width'] = '{}px'.format(self._width)
        if self._height:
            style['height'] = '{}px'.format(self._height)
        return vd.div(self._child, style=style, id='test_id', class_='test_class')


def _save_plot(fig, fname, quality=40):
    from PIL import Image
    from matplotlib import pyplot as plt

    old_display = os.environ.get('DISPLAY', '')
    os.environ['DISPLAY'] = ''

    # dpi = 100
    plt.savefig(fname+'.png', pad_inches=0)  # ,bbox_inches='tight')
    plt.close(fig)
    im = Image.open(fname+'.png').convert('RGB')
    os.remove(fname+'.png')
    im.save(fname, quality=quality)

    if old_display:
        os.environ['DISPLAY'] = old_display


class LazyDiv(vd.Component):
    def __init__(self, child):
        vd.Component.__init__(self)
        self._child = child
        self._has_been_seen = False
        self._div_id = 'LazyDiv-'+str(uuid.uuid4())

    def _on_visible(self):
        self._has_been_seen = True
        self.refresh()

    def render(self):
        try:
            size = self._child.size()  # if it has the size method
        except:
            print('Warning: child of LazyDiv does not have a size() method')
            size = (300, 300)
        div_style = dict()
        div_style['width'] = '{}px'.format(size[0])
        div_style['height'] = '{}px'.format(size[1])
        if self._has_been_seen:
            return vd.div(self._child, style=div_style)
        else:
            callback_id = 'lazydiv-callback-' + str(uuid.uuid4())
            vd.register_callback(callback_id, self._on_visible)
            js = """
            function do_initialize(elmt) {
              var called=false;
              var io = new IntersectionObserver(
                entries => {
                  if (entries[0].isIntersecting) {
                    if (!called) {
                      window.vdomr_invokeFunction('{callback_id}', [], {})
                      called=true;
                      io.disconnect();
                    }
                  }
                },
                {
                  // Using default options.
                }
              );
              io.observe(elmt);
            }
            var num_initialize_tries=0;
            function initialize() {
              num_initialize_tries=num_initialize_tries+1;
              var elmt=document.getElementById('{div_id}');
              if (elmt) {
                do_initialize(elmt);
              }
              else {
                if (num_initialize_tries>100) {
                  console.warn('Problem initializing LazyDiv.');
                  return;
                }
                setTimeout(function() {
                  initialize();
                },500);
              }
            }
            initialize();
            """
            js = self._div_id.join(js.split('{div_id}'))
            js = callback_id.join(js.split('{callback_id}'))
            vd.devel.loadJavascript(js=js, delay=100)
            return vd.div('Loading...', id=self._div_id, style=div_style)

def _is_jsonable(x):
    try:
        json.dumps(x)
        return True
    except (TypeError, OverflowError):
        return False
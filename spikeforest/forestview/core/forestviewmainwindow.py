import vdomr as vd
from .viewcontainer import ViewContainer
from .forestviewcontrolpanel import ForestViewControlPanel
import uuid
import multiprocessing
import traceback
import sys
import time
from mountaintools import client as mt

# HIGH TODO move tabs between north/south containers
# HIGH TODO cross-correlograms widget

class ForestViewMainWindow(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)

        self._context = context
        self._control_panel = ForestViewControlPanel(self._context)
        self._view_container_north = ViewContainer()
        self._view_container_south = ViewContainer()
        self._view_containers = [self._view_container_north, self._view_container_south]
        self._control_panel.onLaunchView(self._trigger_launch_view)

        self._current_view_container = self._view_container_north
        self._view_container_north.onClick(self._on_click_north)
        self._view_container_south.onClick(self._on_click_south)

        #style0 = dict(border='solid 1px gray')
        self._container_CP = Container(self._control_panel, scroll=True)
        self._container_VCN = Container(self._view_container_north)
        self._container_VCS = Container(self._view_container_south)
        self._container_main = Container(self._container_CP, self._container_VCN, self._container_VCS, position_mode='relative')

        self._highlight_view_containers()

        self._size = (1200, 800)

        vd.devel.loadBootstrap()

        self._update_sizes()

    def setSize(self, size):
        self._size = size
        self._update_sizes()

    def size(self):
        return self._size

    def _update_sizes(self):
        width = self._size[0]
        #width1 = int(min(300, width*0.3))
        width1 = 320
        width2 = width-width1-30
        height = self._size[1]
        height1 = int(height/2)-5
        height2 = height-height1-30

        self._container_main.setSize((width,height))
        self._container_main.setPosition((0,0))
        
        self._container_CP.setSize((width1, height-20))
        self._container_CP.setPosition((10,10))
        
        self._container_VCN.setSize((width2, height1))
        self._container_VCN.setPosition((width1+20, 10))

        self._container_VCS.setSize((width2,height2))
        self._container_VCS.setPosition((width1+20,height1+20))

        self._view_container_north.setSize((width2, height1))
        self._view_container_south.setSize((width2, height2))
        

    def _highlight_view_containers(self):
        for VC in [self._view_container_north, self._view_container_south]:
            VC.setHighlight(VC == self._current_view_container)

    def _on_click_north(self):
        self._current_view_container = self._view_container_north
        self._highlight_view_containers()

    def _on_click_south(self):
        self._current_view_container = self._view_container_south
        self._highlight_view_containers()

    def _trigger_launch_view(self, view_launcher):
        if not view_launcher.get('always_open_new', False):
            for VC in self._view_containers:
                v = VC.findView(name=view_launcher.get('name', ''))
                if v:
                    VC.setCurrentView(v)
                    return
        frame = ViewFrame(view_launcher=view_launcher)
        self._current_view_container.addView(frame, name=view_launcher.get('name', ''))
        frame.initialize()

    def context(self):
        return self._context

    def render(self):
        return self._container_main

class TextComponent(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._text = ''
    def setText(self, txt):
        if self._text == txt:
            return
        self._text = txt
        self.refresh()
    def render(self):
        return vd.span(self._text)

class TitleBar(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._title = 'TitleBar'
        self._height = 20
    def setTitle(self, title0):
        if title0 == self._title:
            return
        self._title=title0
        self.refresh()
    def height(self):
        return self._height
    def render(self):
        return vd.div(self._title, style={'height':'{}px'.format(self._height), 'font-size':'14px'})

class ViewFrame(vd.Component):
    def __init__(self, *, view_launcher):
        vd.Component.__init__(self)
        self._view_launcher = view_launcher
        self._connection_to_prepare = None
        self._prepare_log_text = ''
        self._prepare_log_text_view = TextComponent()
        self._title_bar = TitleBar()
        self._view = None
        self._size = (100, 100)
        self._init_process = None
        self.updateTitle()
    def setSize(self, size):
        self._size=size
        self._update_view_size()
    def size(self):
        return self._size
    def tabLabel(self):
        if self._view:
            return self._view.tabLabel()
        else:
            return self._view_launcher['label']+'...'
    def updateTitle(self):
        if self._view:
            if hasattr(self._view, 'title'):
                title0 = self._view.title()
            else:
                title0 = ''
        else:
            title0='Preparing: {} ...'.format(self._view_launcher['label'])
        self._title_bar.setTitle(title0)
    def initialize(self):
        view_launcher = self._view_launcher
        context = view_launcher['context']
        opts = view_launcher['opts']
        view_class = view_launcher['view_class']
        if hasattr(view_class, 'prepareView'):
            self._connection_to_prepare, connection_to_parent = multiprocessing.Pipe()
            self._init_process = multiprocessing.Process(
                target=_prepare_in_worker,
                args=(view_class, context, opts, connection_to_parent, mt.getDownloadFromConfig())
            )
            self._init_process.start()

            self._check_prepare_count = 0
            vd.set_timeout(self._check_prepare, 0.1)
        else:
            if hasattr(context, 'initialize'):
                context.initialize()
            self._view = view_class(context=context, opts=opts)
            self._update_view_size()
            self.updateTitle()
        self.refresh()
    def cleanup(self):
        if self._init_process:
            print('# terminating init process')
            self._init_process.terminate()
        if self._view:
            if hasattr(self._view, 'cleanup'):
                (getattr(self._view, 'cleanup'))()
    def render(self):
        if self._view:
            X = self._view
        else:
            X = vd.components.ScrollArea(
                vd.div(
                    vd.h3('Preparing...'),
                    vd.pre(self._prepare_log_text_view)
                ),
                height=self._size[1] - self._title_bar.height()
            )
        return vd.div(self._title_bar, X)
    def _update_view_size(self):
        size = self._size
        if self._view:
            self._view.setSize((size[0], size[1]-self._title_bar.height()))
    def _check_prepare(self):
        if not self._view:
            if self._connection_to_prepare.poll():
                msg = self._connection_to_prepare.recv()
                if msg['name'] == 'log':
                    self._prepare_log_text = self._prepare_log_text + msg['text']
                    self._prepare_log_text_view.setText(self._prepare_log_text)
                elif msg['name'] == 'result':
                    self._on_prepare_completed(msg['result'])
                    return
            self._check_prepare_count = self._check_prepare_count + 1
            if self._check_prepare_count < 3:
                timeout = 0.2
            elif self._check_prepare_count < 5:
                timeout = 0.5
            elif self._check_prepare_count < 10:
                timeout = 1
            else:
                timeout = 5
            vd.set_timeout(self._check_prepare, timeout)
    def _on_prepare_completed(self, result):
        self._init_process = None
        view_launcher = self._view_launcher
        context = view_launcher['context']
        opts = view_launcher['opts']
        view_class = view_launcher['view_class']
        if hasattr(context, 'initialize'):
            context.initialize()
        self._view = view_class(context=context, opts=opts, prepare_result=result)
        self._update_view_size()
        self.refresh()

class StdoutSender():
    def __init__(self, connection):
        self._connection = connection
        self._handler = _StdoutHandler(connection)
    def __enter__(self):
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        self._handler.setOtherStdout(self._old_stdout)
        sys.stdout = self._handler
        sys.stderr = self._handler
        return dict()
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handler.send()
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr

class _StdoutHandler(object):
    def __init__(self, connection):
        self._connection = connection
        self._text = ''
        self._timer = time.time()
        self._other_stdout = None

    def write(self, data):
        if self._other_stdout:
            self._other_stdout.write(data)
        self._text = self._text + str(data)
        elapsed = time.time() - self._timer
        if elapsed > 5:
            self.send()
            self._timer = time.time()

    def flush(self):
        if self._other_stdout:
            self._other_stdout.flush()

    def setOtherStdout(self, other_stdout):
        self._other_stdout = other_stdout

    def send(self):
        if self._text:
            self._connection.send(dict(name="log", text=self._text))
            self._text=''

def _prepare_in_worker(view_class, context, opts, connection_to_parent, download_from_config):
    mt.setDownloadFromConfig(download_from_config)
    with StdoutSender(connection=connection_to_parent):
        try:
            print('***** Preparing...')
            result0 = view_class.prepareView(context=context, opts=opts)
        except:
            traceback.print_exc()
            raise
    connection_to_parent.send(dict(
        name='result',
        result=result0
    )) 

class Container(vd.Component):
  def __init__(self,*args,position=(0,0),size=(0,0),position_mode='absolute',style=dict(), scroll=False):
    vd.Component.__init__(self)
    self._elmt_id = 'Container-'+str(uuid.uuid4())
    self._children=list(args)
    self._position=position
    self._size=size
    self._position_mode=position_mode
    self._style=style
    self._scroll=scroll
  def setSize(self, size):
    js="""
    document.getElementById('{elmt_id}').style.width='{width}px';
    document.getElementById('{elmt_id}').style.height='{height}px';
    """
    js=js.replace('{elmt_id}',self._elmt_id)
    js=js.replace('{width}',str(size[0]))
    js=js.replace('{height}',str(size[1]))
    self.executeJavascript(js)
  def setPosition(self, position):
    js="""
    document.getElementById('{elmt_id}').style.left='{left}px';
    document.getElementById('{elmt_id}').style.top='{top}px';
    """
    js=js.replace('{elmt_id}',self._elmt_id)
    js=js.replace('{left}',str(position[0]))
    js=js.replace('{top}',str(position[1]))
    self.executeJavascript(js)
  def render(self):
    style=self._style
    style['position']=self._position_mode
    style['width']='{}px'.format(self._size[0])
    style['height']='{}px'.format(self._size[1])
    style['left']='{}px'.format(self._position[0])
    style['top']='{}px'.format(self._position[1])
    if self._scroll:
        style['overflow']='auto'
    else:
        style['overflow']='hidden'
    ret = vd.div(
        self._children,
        style=style,
        id=self._elmt_id
    )
    #if self._scroll:
    #    ret = vd.components.ScrollArea(ret, height=self._size[1])
    return ret
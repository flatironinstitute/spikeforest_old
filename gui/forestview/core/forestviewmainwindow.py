import vdomr as vd
from .viewcontainer import ViewContainer
from .forestviewcontrolpanel import ForestViewControlPanel
import uuid

class ForestViewMainWindow(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)

        self._context = context
        self._control_panel = ForestViewControlPanel(self._context)
        self._view_container_north = ViewContainer()
        self._view_container_south = ViewContainer()
        self._control_panel.onLaunchView(self._trigger_launch_view)

        self._current_view_container = self._view_container_north
        self._view_container_north.onClick(self._on_click_north)
        self._view_container_south.onClick(self._on_click_south)

        #style0 = dict(border='solid 1px gray')
        self._container_CP = Container(self._control_panel)
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

    def addViewLauncher(self, view_launcher):
        self._control_panel.addViewLauncher(view_launcher)

    def _update_sizes(self):
        width = self._size[0]
        width1 = int(min(300, width*0.3))
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
        V = view_launcher['view_class'](self._context)
        self._current_view_container.addView(V)

    def context(self):
        return self._context

    def render(self):
        return self._container_main

class Container(vd.Component):
  def __init__(self,*args,position=(0,0),size=(0,0),position_mode='absolute',style=dict()):
    vd.Component.__init__(self)
    self._elmt_id = 'Container-'+str(uuid.uuid4())
    self._children=list(args)
    self._position=position
    self._size=size
    self._position_mode=position_mode
    self._style=style
  def setSize(self, size):
    js="""
    document.getElementById('{elmt_id}').style.width='{width}px';
    document.getElementById('{elmt_id}').style.height='{height}px';
    """
    js=js.replace('{elmt_id}',self._elmt_id)
    js=js.replace('{width}',str(size[0]))
    js=js.replace('{height}',str(size[1]))
    vd.devel.loadJavascript(js=js)
  def setPosition(self, position):
    js="""
    document.getElementById('{elmt_id}').style.left='{left}px';
    document.getElementById('{elmt_id}').style.top='{top}px';
    """
    js=js.replace('{elmt_id}',self._elmt_id)
    js=js.replace('{left}',str(position[0]))
    js=js.replace('{top}',str(position[1]))
    vd.devel.loadJavascript(js=js)
  def render(self):
    style=self._style
    style['position']=self._position_mode
    style['width']='{}px'.format(self._size[0])
    style['height']='{}px'.format(self._size[1])
    style['left']='{}px'.format(self._position[0])
    style['top']='{}px'.format(self._position[1])
    style['overflow']='hidden'
    return vd.div(
        self._children,
        style=style,
        id=self._elmt_id
    )


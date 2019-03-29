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

        self._highlight_view_containers()

        self._size = (1200, 800)

        vd.devel.loadBootstrap()

    def setSize(self, size):
        self._size = size
        self.refresh()

    def size(self):
        return self._size

    def addViewLauncher(self, name, view_launcher):
        self._control_panel.addViewLauncher(name, view_launcher)

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
        width = self._size[0]
        width1 = int(min(300, width*0.3))
        width2 = width-width1-30
        height = self._size[1]
        height1 = int(height/2)-5
        height2 = height-height1-30
        style0 = dict(border='solid 1px gray')
        W_CP = Container(self._control_panel, position=(
            10, 10), size=(width1, height-20), style=style0)
        self._view_container_north.setSize((width2, height1))
        self._view_container_south.setSize((width2, height2))
        W_VCN = Container(self._view_container_north, position=(
            width1+20, 10), size=(width2, height1), style=style0)
        W_VCS = Container(self._view_container_south, position=(
            width1+20, height1+20), size=(width2, height2), style=style0)
        return Container(W_CP, W_VCN, W_VCS, position=(0, 0), size=(width, height), position_mode='relative')

class Container(vd.Component):
  def __init__(self,*args,position,size,position_mode='absolute',style=dict()):
    vd.Component.__init__(self)
    self._children=list(args)
    self._position=position
    self._size=size
    self._position_mode=position_mode
    self._style=style
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
        style=style
    )


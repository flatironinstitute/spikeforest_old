import vdomr as vd
from .tabbar import TabBar

class HighlightBox(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
    self._highlight=True
  def setHighlight(self,val):
    if self._highlight==val:
        return
    self._highlight=val
    self.refresh()
  def render(self):
    style0=dict(width='100%',height='100%',position='absolute')
    style0['z-index']='-1'
    if self._highlight:
        style0['border']='solid 2px black'
    return vd.div(style=style0)

class ViewFrame(vd.Component):
  def __init__(self,child):
    vd.Component.__init__(self)
    self._child=child
  def child(self):
    return self._child
  def render(self):
    return vd.div(self._child)

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
    return vd.div(
        self._children,
        style=style
    )

class ViewContainer(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
    self._views=[]
    self._view_frames=[]
    self._current_frame=None
    self._size=(0,0)
    self._tab_bar=TabBar()
    self._tab_bar.onCurrentTabChanged(self._on_current_tab_changed)
    self._click_handlers=[]
    self._highlight_box=HighlightBox()
  def onClick(self,handler):
    self._click_handlers.append(handler)
  def setSize(self,size):
    self._size=size
    for view in self._views:
      self._update_view_size(view)
  def addView(self,view):
    self._update_view_size(view)
    frame=ViewFrame(view)
    self._views.append(view)
    self._view_frames.append(frame)
    self._tab_bar.addTab(view,view.tabLabel())
    self._current_frame=frame
    self.refresh()
  def setHighlight(self,val):
    self._highlight_box.setHighlight(val)

  def _update_view_size(self, view):
    view.setSize((self._size[0]-self._tab_bar.height()-10,self._size[1]-self._tab_bar.height()-10))

  def _on_current_tab_changed(self):
    self._current_frame=self._tab_bar.currentTabKey()
    self.refresh()
  def currentView(self):
    f=self._current_frame
    if not f:
      return None
    return f.child()
  def _on_click(self):
    for handler in self._click_handlers:
      handler()
  def render(self):
    f=self._current_frame
    style0=dict(width='100%',height='100%',position='absolute')
    style1=dict(left='5px',right='5px',top='5px',bottom='5px',position='absolute')
    onclick=self._on_click
    if not f:
      style1['background-color']='lightgray'
      f=''
    return vd.div(self._highlight_box,vd.div(f,style=style1),self._tab_bar,style=style0,onclick=onclick)

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

class ViewHolder(vd.Component):
  def __init__(self,child, *, name=''):
    vd.Component.__init__(self)
    self._child=child
    self._name=name
  def name(self):
    return self._name
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

class ViewContainerContent(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
    self._child = None
  def setChild(self, child):
    self._child = child
    self.refresh()
  def render(self):
    if not self._child:
      return vd.div('No content')
    return self._child

class ViewContainer(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
    self._views=dict()
    self._fiew_holders=dict()
    self._content=ViewContainerContent()
    self._last_id_num=0
    self._size=(0,0)
    self._tab_bar=TabBar()
    self._tab_bar.onCurrentTabChanged(self._on_current_tab_changed)
    self._tab_bar.onTabRemoved(self._on_tab_removed)
    self._click_handlers=[]
    self._highlight_box=HighlightBox()
    self._poll()
  def onClick(self,handler):
    self._click_handlers.append(handler)
  def setSize(self,size):
    self._size=size
    for view in self._views.values():
      self._update_view_size(view)
  def addView(self,view, *, name=''):
    id_num = self._last_id_num+1
    self._last_id_num = self._last_id_num + 1
    view_id = 'view_{}'.format(id_num)

    self._update_view_size(view)
    holder=ViewHolder(view, name=name)
    self._views[view_id]=view
    self._fiew_holders[view_id] = holder
    self._tab_bar.addTab(view_id, view.tabLabel())

    # self.refresh()
  def findView(self, *, name):
    for vf in self._fiew_holders.values():
      if vf.name() == name:
        return vf.child()
    return None
  def setCurrentView(self, view):
    for id, v in self._views.items():
      if v == view:
        self._tab_bar.setCurrentTab(id=id)
        return

  def setHighlight(self,val):
    self._highlight_box.setHighlight(val)

  def _update_view_size(self, view):
    view.setSize((self._size[0]-self._tab_bar.height()-10,self._size[1]-self._tab_bar.height()-10))

  def _on_current_tab_changed(self):
    id = self._tab_bar.currentTabId()
    if id:
      holder = self._fiew_holders[id]
      self._content.setChild(holder)
    else:
      self._content.setChild(None)

  def _on_tab_removed(self, id):
    if id in self._views:
      view = self._views[id]
      del self._views[id]
      del self._fiew_holders[id]
      if hasattr(view, 'cleanup'):
        (getattr(view, 'cleanup'))()

  def currentView(self):
    id = self._tab_bar.currentTabId()
    if id is None:
      return None
    if id not in self._views:
      return None
    return self._views[id]
  def _on_click(self):
    for handler in self._click_handlers:
      handler()
  def _poll(self):
    for id, v in self._views.items():
      label = v.tabLabel()
      self._tab_bar.setTabLabel(id, label)
      if hasattr(v, 'updateTitle'):
        v.updateTitle()
    vd.set_timeout(self._poll, 2)
  def render(self):
    style_outer=dict(width='100%',height='100%',position='absolute')
    style_content=dict(left='5px',right='5px',top='{}px'.format(5+self._tab_bar.height()),bottom='5px',position='absolute')
    onclick=self._on_click
    return vd.div(self._highlight_box,vd.div(self._content, id='content-'+self.componentId(),style=style_content),self._tab_bar,style=style_outer,onclick=onclick)

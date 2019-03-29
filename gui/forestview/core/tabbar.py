import vdomr as vd

class TabBarTab(vd.Component):
  def __init__(self,*,height,label,key):
    vd.Component.__init__(self)
    self._height=height
    self._label=label
    self._click_handlers=[]
    self._selected=False
    self._key=key
  def key(self):
    return self._key
  def setSelected(self,selected):
    self._selected=selected
    self.refresh()
  def onClick(self,handler):
    self._click_handlers.append(handler)
  def _on_click(self):
    for handler in self._click_handlers:
      handler()
  def render(self):
    style=dict(
        border='solid 1px gray',
        height='{}px'.format(self._height),
        cursor='pointer'
    )
    classes='tabbartab'
    if self._selected:
      classes=classes+' selected'
    return vd.div(self._label,style=style,class_=classes,onclick=self._on_click)

class TabBar(vd.Component):
  def __init__(self,height=25):
    vd.Component.__init__(self)
    self._height=height
    self._tabs=[]
    self._current_tab=None
    self._current_tab_changed_handlers=[]

    vd.devel.loadCss(css=_CSS)

  def height(self):
    return self._height
  def onCurrentTabChanged(self,handler):
    self._current_tab_changed_handlers.append(handler)
  def setCurrentTab(self,tab):
    if tab==self._current_tab:
      return
    self._current_tab=tab
    for tab in self._tabs:
      if tab==self._current_tab:
        tab.setSelected(True)
      else:
        tab.setSelected(False)
    for handler in self._current_tab_changed_handlers:
      handler()
  def currentTabKey(self):
    if not self._current_tab:
      return None
    return self._current_tab.key()
  def addTab(self,key,label):
    tab=TabBarTab(height=self._height,label=label,key=key)
    def set_current_tab():
      self.setCurrentTab(tab)
      self.refresh()
    tab.onClick(set_current_tab)
    self._tabs.append(tab)
    self.setCurrentTab(tab)
    self.refresh()
  def render(self):
    style0=dict(
        position='absolute',
        left='0px',
        bottom='0px',
        height='{}px'.format(self._height)
    )
    divs=[vd.div(tab,style={'float':'left'}) for tab in self._tabs]
    return vd.div(divs,style=style0)

_CSS = """
.tabbartab {
  background-color:lightgray;
  padding:3px;
}
.tabbartab:hover {
  background-color:rgb(240,240,240);
}
.tabbartab.selected {
  background-color:white;
  color:green;
}
"""
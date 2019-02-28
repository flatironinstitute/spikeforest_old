import vdomr as vd
from spikeforest import spiketoolkit as st
from spikeforest import spikeextractors as se
from .unitwaveformswidget import UnitWaveformsWidget
from .correlogramswidget import CorrelogramsWidget
from .timeserieswidget import TimeseriesWidget

class ButtonList(vd.Component):
    def __init__(self,data):
        vd.Component.__init__(self)
        self._data=data
    def render(self):
        button_style={'margin':'3px'}
        buttons=[
            vd.button(item[0],onclick=item[1],style=button_style)
            for item in self._data
        ]
        return vd.div(buttons)
      
class ScrollArea(vd.Component):
  def __init__(self,child,*,size):
    vd.Component.__init__(self)
    self._child=child
    self._size=size
  def render(self):
    return vd.div(self._child,style=dict(overflow='auto',width='{}px'.format(self._size[0]),height='{}px'.format(self._size[1])))

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

class ViewLauncher(vd.Component):
  def __init__(self,context,view_classes):
    vd.Component.__init__(self)
    self._context=context
    self._registered_view_classes=view_classes
    self._launch_view_handlers=[]
  def render(self):
    list=[
        (VC.LABEL,self._create_launch_function(VC))
        for VC in self._registered_view_classes
    ]
    list1=ButtonList(list)
    return vd.div(
        list1
    )
  def onLaunchView(self,handler):
    self._launch_view_handlers.append(handler)
  def _create_launch_function(self,view_class):
    def launch():
      for handler in self._launch_view_handlers:
        handler(view_class)
    return launch

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
  
class ViewContainer(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
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
  def addView(self,view):
    view.setSize((self._size[0]-self._tab_bar.height()-10,self._size[1]-self._tab_bar.height()-10))
    frame=ViewFrame(view)
    self._view_frames.append(frame)
    self._tab_bar.addTab(view,view.tabLabel())
    self._current_frame=frame
    self.refresh()
  def setHighlight(self,val):
    self._highlight_box.setHighlight(val)
  def _current_frame(self):
    return self._current_frame
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

class VIEW_GeneralInfo(vd.Component):
  LABEL='General info'
  def __init__(self,context):
    vd.Component.__init__(self)
    self._context=context
    self._size=(300,300)
  def tabLabel(self):
    return 'General info'
  def setSize(self,size):
    self._size=size
  def render(self):
    rec=self._context.recording
    res=self._context.sorting_result
    
    rows=[]
    rows.append(vd.tr(
        vd.th('Study'),vd.td(rec.study().name())
    ))
    rows.append(vd.tr(
        vd.th('Recording'),vd.td(rec.name())
    ))
    rows.append(vd.tr(
        vd.th('Directory'),vd.td(rec.directory())
    ))
    true_units=rec.trueUnitsInfo(format='json')
    rows.append(vd.tr(
        vd.th('Num. true units'),vd.td('{}'.format(len(true_units)))
    ))
    RX=rec.recordingExtractor()
    rows.append(vd.tr(
        vd.th('Num. channels'),vd.td('{}'.format(len(RX.getChannelIds())))
    ))
    rows.append(vd.tr(
        vd.th('Samplerate'),vd.td('{}'.format(RX.getSamplingFrequency()))
    ))

    recording_file_is_local=rec.recordingFileIsLocal()
    if recording_file_is_local:
        elmt='True'
    else:
        elmt=vd.span('False',' ',vd.a('(download)',onclick=self._on_download_recording_file))
    rows.append(vd.tr(
        vd.th('raw.mda is downloaded'),vd.td(elmt))
    )

    firings_true_file_is_local=rec.firingsTrueFileIsLocal()
    if firings_true_file_is_local:
        elmt='True'
    else:
        elmt=vd.span('False',' ',vd.a('(download)',onclick=self._on_download_firings_true_file))
    rows.append(vd.tr(
        vd.th('firings_true.mda is downloaded'),vd.td(elmt))
    )

    if res:
        rows.append(vd.tr(
            vd.th('Sorting result'),vd.td(res.sorterName())
        ))
        sorting=res.sorting()
        rows.append(vd.tr(
            vd.th('Num. sorted units'),vd.td('{}'.format(len(sorting.getUnitIds())))
        ))

    table=vd.table(rows,style={'text-align':'left','width':'auto','font-size':'13px'},class_='table')
    
    return ScrollArea(vd.div(table),size=self._size)
        
class VIEW_Timeseries(vd.Component):
  LABEL='Timeseries'
  def __init__(self,context):
    vd.Component.__init__(self)
    self._context=context
    rx=self._context.recording.recordingExtractor()
    sf=rx.getSamplingFrequency()
    print(self._context.recording.recordingFileIsLocal())
    if self._context.recording.recordingFileIsLocal():
        rx=se.SubRecordingExtractor(parent_recording=rx,start_frame=int(sf*0),end_frame=int(sf*10))
    else:
        rx=se.SubRecordingExtractor(parent_recording=rx,start_frame=int(sf*0),end_frame=int(sf*1))
    rx=st.preprocessing.bandpass_filter(recording=rx,freq_min=300,freq_max=6000)
    self._timeseries_widget=TimeseriesWidget(recording=rx)
  def tabLabel(self):
    return 'Timeseries'
  def setSize(self,size):
    self._timeseries_widget.setSize(size)
  def render(self):
    return vd.div(self._timeseries_widget)
  
class VIEW_TrueUnitWaveforms(vd.Component):
  LABEL='True waveforms'
  def __init__(self,context):
    vd.Component.__init__(self)
    self._context=context
    rx=self._context.recording.recordingExtractor()
    sf=rx.getSamplingFrequency()
    rx=st.preprocessing.bandpass_filter(recording=rx,freq_min=300,freq_max=6000)
    sx=self._context.recording.sortingTrue()
    self._widget=UnitWaveformsWidget(recording=rx,sorting=sx)
    self._size=(300,300)
    self._update_selection()
    self._context.onSelectionChanged(self._update_selection)
  def _update_selection(self):
    self._widget.setSelectedUnitIds(self._context.selectedTrueUnitIds())
  def tabLabel(self):
    return 'True waveforms'
  def setSize(self,size):
    self._size=size
    self.refresh()
  def render(self):
    return ScrollArea(self._widget,size=self._size)
  
class VIEW_UnitWaveforms(vd.Component):
  LABEL='Waveforms'
  def __init__(self,context):
    vd.Component.__init__(self)
    self._context=context
    rx=self._context.recording.recordingExtractor()
    sf=rx.getSamplingFrequency()
    rx=st.preprocessing.bandpass_filter(recording=rx,freq_min=300,freq_max=6000)
    sx=self._context.sorting_result.sorting()
    self._widget=UnitWaveformsWidget(recording=rx,sorting=sx)
    self._size=(300,300)
    self._update_selection()
    self._context.onSelectionChanged(self._update_selection)
  def _update_selection(self):
    self._widget.setSelectedUnitIds(self._context.selectedUnitIds())
  def tabLabel(self):
    return 'Waveforms'
  def setSize(self,size):
    self._size=size
    self.refresh()
  def render(self):
    return ScrollArea(self._widget,size=self._size)
  
class VIEW_TrueAutocorrelograms(vd.Component):
  LABEL='True autocorrelograms'
  def __init__(self,context):
    vd.Component.__init__(self)
    self._context=context
    rx=self._context.recording.recordingExtractor()
    sf=rx.getSamplingFrequency()
    sx=self._context.recording.sortingTrue()
    self._widget=CorrelogramsWidget(sorting=sx,samplerate=sf)
    self._size=(300,300)
    self._update_selection()
    self._context.onSelectionChanged(self._update_selection)
  def _update_selection(self):
    self._widget.setSelectedUnitIds(self._context.selectedTrueUnitIds())
  def tabLabel(self):
    return 'True autocorrelograms'
  def setSize(self,size):
    self._size=size
    self.refresh()
  def render(self):
    return ScrollArea(self._widget,size=self._size)

  
class VIEW_Autocorrelograms(vd.Component):
  LABEL='Autocorrelograms'
  def __init__(self,context):
    vd.Component.__init__(self)
    self._context=context
    rx=self._context.recording.recordingExtractor()
    sf=rx.getSamplingFrequency()
    sx=self._context.sorting_result.sorting()
    self._widget=CorrelogramsWidget(sorting=sx,samplerate=sf)
    self._size=(300,300)
    self._update_selection()
    self._context.onSelectionChanged(self._update_selection)
  def _update_selection(self):
    self._widget.setSelectedUnitIds(self._context.selectedUnitIds())
  def tabLabel(self):
    return 'Autocorrelograms'
  def setSize(self,size):
    self._size=size
    self.refresh()
  def render(self):
    return ScrollArea(self._widget,size=self._size)

class Context():
  def __init__(self):
    sorting_result=None
    recording=None
    self._selected_true_unit_ids=[]
    self._selected_unit_ids=[]
    self._selection_changed_handlers=[]
  def selectedTrueUnitIds(self):
    return self._selected_true_unit_ids
  def selectedUnitIds(self):
    return self._selected_unit_ids
  def setSelectedTrueUnitIds(self,ids):
    self._selected_true_unit_ids=ids
    for handler in self._selection_changed_handlers:
      handler()
  def setSelectedUnitIds(self,ids):
    self._selected_unit_ids=ids
    for handler in self._selection_changed_handlers:
      handler()
  def onSelectionChanged(self,handler):
    self._selection_changed_handlers.append(handler)

def _f3(num):
  return '{:.5g}'.format(float(num))

class CheckBox(vd.Component):
    def __init__(self,checked=False,onchange=None,**kwargs):
        vd.Component.__init__(self)
        self._kwargs=kwargs
        self._checked=checked
        self._on_change_handlers=[]
        if onchange:
          self._on_change_handlers.append(onchange)
    def checked(self):
      return self._checked
    def setChecked(self,val):
        self._checked=val
        self.refresh()
    def onChange(self,handler):
        self._on_change_handlers.append(handler)
    def _onchange(self,value): # somehow the value is useless here, so we just toggle
        self._checked = (not self._checked)
        for handler in self._on_change_handlers:
          handler()
    def render(self):
        attrs=dict()
        if self._checked:
          attrs['checked']='checked'
        X=vd.input(type='checkbox',**attrs,onchange=self._onchange,**self._kwargs)
        return X
      
class Table(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
    self._column_labels=[]
    self._rows=[]
    self._size=(300,300)
    self._selection_mode='none' # 'none', 'single', 'multiple'
    self._selection_changed_handlers=[]
  def setColumnLabels(self,labels):
    self._column_labels=labels
  def clearRows(self):
    self._rows=[]
  def addRow(self,*,id,values):
    cb=CheckBox(onchange=self._on_checkbox_changed)
    row0=dict(
        values=values,
        id=id,
        checkbox=cb
    )
    self._rows.append(row0)
  def setSize(self,size):
    self._size=size
  def setSelectionMode(self,mode):
    self._selection_mode=mode
  def selectedRowIds(self):
    ret=[]
    for row in self._rows:
      if row['checkbox'].checked():
        ret.append(row['id'])
    return ret
  def setSelectedRowIds(self,ids):
    for row in self._rows:
      row['checkbox'].setChecked(row['id'] in ids)
  def onSelectionChanged(self,handler):
    self._selection_changed_handlers.append(handler)
  def _on_checkbox_changed(self):
    for handler in self._selection_changed_handlers:
      handler()
  def render(self):
    self._checkboxes=[]
    rows=[]
    elmts=[vd.th(val) for val in self._column_labels]
    if self._selection_mode=='multiple':
      elmts = [vd.th('')] + elmts
    rows.append(vd.tr(elmts))
    for row in self._rows:
      elmts=[vd.td(str(val)) for val in row['values']]
      if self._selection_mode=='multiple':
        elmts = [vd.td(row['checkbox'])] + elmts
      rows.append(vd.tr(elmts))
    table=vd.table(rows,class_='table')
    return ScrollArea(vd.div(table),size=self._size)

class VIEW_TrueUnitsTable(Table):
  LABEL='True units table'
  def __init__(self,context):
    Table.__init__(self)
    self.setSelectionMode('multiple')
    self._context=context
    try:
      self._true_units_info=context.recording.trueUnitsInfo(format='json')
      self._comparison_by_unit=dict()
      SR=self._context.sorting_result
      cwt_list=SR.comparisonWithTruth(format='json')
      for i in cwt_list:
        item=cwt_list[i]
        self._comparison_by_unit[item['unit_id']]=item
    except Exception as err:
      print('warning: ',err)
      self._true_units_info=None    
    self.onSelectionChanged(self._on_selection_changed)
    self._context.onSelectionChanged(self._update_selection)
    self._update()
  def _update_selection(self):
    self.setSelectedRowIds(self._context.selectedTrueUnitIds())
  def tabLabel(self):
    return 'True units'
  def _on_selection_changed(self):
    self._context.setSelectedTrueUnitIds(self.selectedRowIds())
  def _update(self):
    self.setColumnLabels([
        'Unit ID','SNR','Peak channel',
        'Num. events','Firing rate','Accuracy',
        'Best unit','Matched unit',
        'False neg rate','False pos rate',
        'Num matches','Num false neg','Num false pos'
    ])
    self.clearRows()
    if not self._true_units_info:
        print('WARNING: _true_units_info is null.')
        return
    for unit in self._true_units_info:
        unit_id=unit['unit_id']
        if unit_id in self._comparison_by_unit:
          item=self._comparison_by_unit[unit_id]
          accuracy=item['accuracy']
          best_unit=item['best_unit']
          matched_unit=item['matched_unit']
          f_n=item['f_n']
          f_p=item['f_p']
          num_matches=item['num_matches']
          num_false_negatives=item.get('num_false_negatives','')
          num_false_positives=item.get('num_false_positives','')
        else:
          accuracy=''
          best_unit=''
          matched_unit=''
          f_n=''
          f_p=''
          num_matches=''
          num_false_negatives=''
          num_false_positives=''
        self.addRow(
            id=unit_id,
            values=[
              unit_id,
              _f3(unit['snr']),
              unit['peak_channel'],
              unit['num_events'],
              _f3(unit['firing_rate']),
              _f3(accuracy),
              best_unit,
              matched_unit,
              _f3(f_n),
              _f3(f_p),
              num_matches,
              num_false_negatives,
              num_false_positives
            ]
        )
    self._update_selection()
    self.refresh()

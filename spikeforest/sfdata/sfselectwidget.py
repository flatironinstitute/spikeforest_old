import vdomr as vd

class SelectBox(vd.Component):
    def __init__(self,options=[]):
        vd.Component.__init__(self)
        self._on_change_handlers=[]
        self._value=None
        self.setOptions(options)
        
    def setOptions(self,options):
        self._options=options
        if self._value not in options:
          self._value=options[0] if options else None
        self.refresh()
        
    def value(self):
        return self._value
    
    def setValue(self,value):
        self._value=value
        self.refresh()
        
    def onChange(self,handler):
        self._on_change_handlers.append(handler)
        
    def _on_change(self,value):
        self._value=value
        for handler in self._on_change_handlers:
            handler(value=value)
        
    def render(self):
        opts=[]
        for option in self._options:
            if option==self._value:
              opts.append(vd.option(option,selected='selected'))
            else:
              opts.append(vd.option(option))
        X=vd.select(opts,onchange=self._on_change)
        return X

class SFSelectWidget(vd.Component):
  def __init__(self,sfdata,mode):
    vd.Component.__init__(self)
    self._on_change_handlers=[]
    self._SF=sfdata
    self._study_box=SelectBox()
    self._recording_box=SelectBox()
    self._sorting_result_box=SelectBox()
    self._mode=mode

    self._study_box.onChange(self._on_change)
    self._recording_box.onChange(self._on_change)
    self._sorting_result_box.onChange(self._on_change)

  def onChange(self,handler):
    self._on_change_handlers.append(handler)

  def _on_change(self,value):
    self.refresh()
    for handler in self._on_change_handlers:
      handler()
  def study(self):
    name=self._study_box.value()
    return self._SF.study(name) if name else None
  def recording(self):
    study=self.study()
    if not study:
      return None
    name=self._recording_box.value()
    return study.recording(name) if name else None
  def sortingResult(self):
    recording=self.recording()
    if not recording:
      return None
    name=self._sorting_result_box.value()
    return recording.sortingResult(name) if name else None
  def setStudyName(self,name):
    self._study_box.setValue(name)
  def setRecordingName(self,name):
    self._recording_box.setValue(name)
  def setSortingResultName(self,name):
    self._sorting_result_box.setValue(name)
  def render(self):
    self._study_box.setOptions(self._SF.studyNames())
    study=self.study()
    if study:
      self._recording_box.setOptions(study.recordingNames())
      recording=self.recording()
      if recording:
        self._sorting_result_box.setOptions(recording.sortingResultNames())
      else:
        self._sorting_result_box.setOptions([])
    else:
      self._recording_box.setOptions([])
      self._sorting_result_box.setOptions([])

    study_row=vd.tr(vd.td('Study **: '),vd.td(self._study_box))
    recording_row=vd.tr(vd.td('Recording: '),vd.td(self._recording_box))
    sorting_result_row=vd.tr(vd.td('Sorting result: '),vd.td(self._sorting_result_box))
    
    rows=[]
    mode=self._mode
    if mode=='study':
      rows=[study_row]
    elif mode=='recording':
      rows=[study_row,recording_row]
    elif mode=='sorting_result':
      rows=[study_row,recording_row,sorting_result_row]
    else:
      raise Exception('Invalid mode: '+mode)
    
    Table=vd.table(*rows)
    div=vd.div(
      vd.hr(),
      Table,
      vd.hr(),
    )

    return div
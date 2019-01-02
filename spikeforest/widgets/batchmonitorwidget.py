from kbucket import client as kb
import batcho
import vdomr as vd

class ScrollArea(vd.Component):
  def __init__(self,child,*,height):
    vd.Component.__init__(self)
    self._child=child
    self._height=height
  def render(self):
    return vd.div(self._child,style=dict(overflow='auto',height='{}px'.format(self._height)))

class SelectListBox(vd.Component):
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

    def index(self):
        return self._options.index(self._value)
    
    def setValue(self,value):
        self._value=value
        self.refresh()
        
    def onChange(self,handler):
        self._on_change_handlers.append(handler)
        
    #def _on_change(self,value):
    #    self._value=value
    #    for handler in self._on_change_handlers:
    #        handler(value=value)

    def _on_item_clicked(self,option):
      self._value=option
      self.refresh()
      for handler in self._on_change_handlers:
        handler(value=option)

    def _create_option_element(self,option):
      return vd.span(option,onclick=lambda: self._on_item_clicked(option))
        
    def render(self):
        rows=[]
        style_highlight={'background-color':'yellow'}
        for option in self._options:
            elmt=self._create_option_element(option)
            if option==self._value:
              rows.append(vd.tr(vd.td(elmt),style=style_highlight))
            else:
              rows.append(vd.tr(vd.td(elmt)))
        X=vd.table(rows)
        #X=vd.select(opts,onchange=self._on_change)
        return X

class JobStatusWidget(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
    self._job=None
    self._show_console_output_button=vd.button('Show console output',onclick=self._on_show_console_output)
  def setJob(self,job,batch_name,job_index):
    self._job=job
    self._batch_name=batch_name
    self._job_index=job_index
    self._job_status=batcho.get_batch_job_statuses(batch_name=self._batch_name,job_index=self._job_index)[0]
    self._job_console_output=None
    self.refresh()
  def _on_show_console_output(self):
    self._job_console_output=batcho.get_batch_job_console_output(batch_name=self._batch_name,job_index=self._job_index)
    if not self._job_console_output:
      self._job_console_output=''
    self.refresh()
  def render(self):
    if not self._job:
      return vd.div('none')
    status=self._job_status.get('status')
    if not status:
      status='unknown'
    if self._job_console_output is not None:
      #contenteditable is used to enable ctrl+a select
      console_output_elmt=vd.div(vd.pre(self._job_console_output),style={'background':'black','color':'white'},contenteditable="true")
    else:
      console_output_elmt=self._show_console_output_button
    table=vd.table(
        vd.tr(vd.td('Status:'),vd.td(status))
    )
    out=vd.div(console_output_elmt,style=dict(overflow='auto',height='300px'))
    ret=vd.div(
        vd.h3(self._job['label']),
        table,
        out
    )
    return ret

class BatchMonitorWidget(vd.Component):
  def __init__(self,batch_names,height=300):
    vd.Component.__init__(self)
    self._batch_names=batch_names
    self._SEL_batch=vd.components.SelectBox(options=self._batch_names)
    self._SEL_batch.onChange(self._on_batch_changed)
    self._SEL_jobs=SelectListBox(options=[])
    self._SEL_jobs.onChange(self._on_job_changed)
    self._job_status_widget=JobStatusWidget()
    self._jobs=[]
    self._height=height
    self._update_jobs()
  def _on_batch_changed(self,value):
    self._update_jobs()
  def _on_job_changed(self,value):
    job=self._jobs[self._SEL_jobs.index()]
    self._job_status_widget.setJob(job,batch_name=self._SEL_batch.value(),job_index=self._SEL_jobs.index())
  def _update_jobs(self):
    jobs=batcho.get_batch_jobs(batch_name=self._SEL_batch.value())
    self._SEL_jobs.setOptions(['{}: {}'.format(i,jobs[i]['label']) for i in range(len(jobs))])
    self._jobs=jobs
    self._on_job_changed(self._SEL_jobs.value())
  def render(self):
    ret=vd.div(
      vd.h2('Batch Monitor'),
      vd.table(
        vd.tr(
          vd.td('Batch:'),vd.td(self._SEL_batch)
        )
      ),
      vd.table(
        vd.tr(
          vd.td(ScrollArea(self._SEL_jobs,height=self._height),style={'vertical-align':'top','min-width':'400px'}),
          vd.td(ScrollArea(self._job_status_widget,height=self._height),style={'vertical-align':'top'})
        )
      )
    )
    return ret
    
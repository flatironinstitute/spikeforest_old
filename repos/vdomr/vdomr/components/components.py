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

class Button(vd.Component):
    def __init__(self,label,onclick=None,**kwargs):
        vd.Component.__init__(self)
        self._label=label
        self._on_click_handlers=[]
        self._kwargs=kwargs
        if onclick:
            self.onClick(onclick)
    def onClick(self,handler):
        self._on_click_handlers.append(handler)
    def label(self):
        return self._label
    def setLabel(self,label):
        self._label=label
        self.refresh()
    def _on_click(self):
        for handler in self._on_click_handlers:
            handler()
    def render(self):
        button=vd.button(self._label,onclick=self._on_click,**self._kwargs)
        return button

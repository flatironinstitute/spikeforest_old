import uuid
from spikeforest import mdaio
import io
import base64
import vdomr as vd
import os
import numpy as np
import mtlogging
import time
import traceback

source_path=os.path.dirname(os.path.realpath(__file__))

def _mda32_to_base64(X):
    f=io.BytesIO()
    mdaio.writemda32(X,f)
    return base64.b64encode(f.getvalue()).decode('utf-8')

class TemplateWidget(vd.Component):
    def __init__(self,*,template,size=(200,200)):
        vd.Component.__init__(self)

        vd.devel.loadBootstrap()
        vd.devel.loadCss(url='https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css')
        vd.devel.loadJavascript(path=source_path+'/mda.js')
        vd.devel.loadJavascript(path=source_path+'/canvaswidget.js')
        vd.devel.loadJavascript(path=source_path+'/templatewidget.js')
        vd.devel.loadJavascript(path=source_path+'/../dist/jquery-3.3.1.min.js')

        self._div_id='TemplateWidget-'+str(uuid.uuid4())
        self._template = template
        self._template_b64=_mda32_to_base64(self._template)
        self._y_scale_factor=None

        self._size=size
    def setYScaleFactor(self, scale_factor):
        self._y_scale_factor=scale_factor
        self.refresh()
    def setSize(self,size):
        if self._size==size:
            return
        self._size=size
        self.refresh()
    def size(self):
        return self._size
    def render(self):
        div=vd.div(id=self._div_id)
        return div
    def postRenderScript(self):
        js="""
        let W=new window.TemplateWidget();
        let X=new window.Mda();
        X.setFromBase64('{template_b64}');
        W.setTemplate(X);
        W.setSize({width},{height});
        W.setYScaleFactor({y_scale_factor});
        $('#{div_id}').empty();
        $('#{div_id}').css({width:'{width}px',height:'{height}px'})
        $('#{div_id}').append(W.element());
        """
        js = js.replace('{template_b64}', self._template_b64)
        js = js.replace('{div_id}', self._div_id)
        js = js.replace('{width}', str(self._size[0]))
        js = js.replace('{height}', str(self._size[1]))
        js = js.replace('{y_scale_factor}', str(self._y_scale_factor or 'null'))
        return js
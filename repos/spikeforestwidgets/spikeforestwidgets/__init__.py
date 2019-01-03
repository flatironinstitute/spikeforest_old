import uuid
from spikeextractors import mdaio
import io
import base64
import vdomr as vd
import os

source_path=os.path.dirname(os.path.realpath(__file__))

def _mda32_to_base64(X):
    f=io.BytesIO()
    mdaio.writemda32(X,f)
    return base64.b64encode(f.getvalue()).decode('utf-8')

class TimeseriesWidget(vd.Component):
    def __init__(self,*,recording):
        vd.Component.__init__(self)
        self._recording=recording
        self._array=recording.getTraces()
        self._array_b64=_mda32_to_base64(self._array)
        self._div_id='SFTimeseriesWidget-'+str(uuid.uuid4())

        vd.devel.loadBootstrap()
        vd.devel.loadCss(url='https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css')
        vd.devel.loadJavascript(path=source_path+'/dist/main.js')
        vd.devel.loadJavascript(path=source_path+'/dist/d3.v5.min.js')
        vd.devel.loadJavascript(path=source_path+'/dist/jquery-3.3.1.min.js')

        js="window.sfdata=window.sfdata||{}; window.sfdata.test=1; window.sfdata['array_b64_{div_id}']='{b64}'"
        js=self._div_id.join(js.split('{div_id}'))
        js=self._array_b64.join(js.split('{b64}'))
        vd.devel.loadJavascript(js=js)
    def render(self):
        div=vd.div(id=self._div_id)
        js="""
        function _base64ToArrayBuffer(base64) {
            var binary_string =  window.atob(base64);
            var len = binary_string.length;
            var bytes = new Uint8Array( len );
            for (var i = 0; i < len; i++)        {
                bytes[i] = binary_string.charCodeAt(i);
            }
            return bytes.buffer;
        }
        let W=new window.TimeseriesWidget();
        let X=_base64ToArrayBuffer(window.sfdata['array_b64_{div_id}']);
        let A=new window.Mda();
        A.setFromArrayBuffer(X);
        let TS=new window.TimeseriesModel(A);
        W.setTimeseriesModel(TS);
        W.setSize(800,400)
        $('#{div_id}').append(W.div());
        """
        js=self._div_id.join(js.split('{div_id}'))
        vd.devel.loadJavascript(js=js,delay=1)
        return div
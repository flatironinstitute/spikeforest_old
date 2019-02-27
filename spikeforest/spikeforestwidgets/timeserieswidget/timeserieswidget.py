import uuid
from spikeforest.spikeextractors import mdaio
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
        vd.devel.loadJavascript(path=source_path+'/mda.js')
        vd.devel.loadJavascript(path=source_path+'/timeseriesmodel.js')
        vd.devel.loadJavascript(path=source_path+'/canvaswidget.js')
        vd.devel.loadJavascript(path=source_path+'/timeserieswidget.js')
        vd.devel.loadJavascript(path=source_path+'/../dist/jquery-3.3.1.min.js')

        js="window.sfdata=window.sfdata||{}; window.sfdata.test=1; window.sfdata['array_b64_{div_id}']='{b64}'"
        js=self._div_id.join(js.split('{div_id}'))
        js=self._array_b64.join(js.split('{b64}'))
        print(self._array.shape)
        print('length of b64: {}'.format(len(self._array_b64)))
        vd.devel.loadJavascript(js=js)
        self._size=(800,400)
    def setSize(self,size):
        print('setSize')
        if self._size==size:
            return
        self._size=size
        self.refresh()
    def render(self):
        print('rendering timeserieswidget...')
        div=vd.div(id=self._div_id)
        js="""
        console.log('testing 111');
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
        //W.setTimeseriesModel(new window.TestTimeseriesModel());
        let X=_base64ToArrayBuffer(window.sfdata['array_b64_{div_id}']);
        let A=new window.Mda();
        A.setFromArrayBuffer(X);
        let TS=new window.TimeseriesModel(A);
        W.setTimeseriesModel(TS);
        W.setSize({width},{height})
        $('#{div_id}').empty();
        $('#{div_id}').css({width:'{width}px',height:'{height}px'})
        $('#{div_id}').append(W.element());
        """
        js=self._div_id.join(js.split('{div_id}'))
        js=js.replace('{width}',str(self._size[0]))
        js=js.replace('{height}',str(self._size[1]))
        js='{}'.format(self._recording.getSamplingFrequency()).join(js.split('{samplerate}'))
        vd.devel.loadJavascript(js=js,delay=1)
        return div

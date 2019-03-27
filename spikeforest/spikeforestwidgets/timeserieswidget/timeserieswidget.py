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
    def __init__(self,*,recording,sorting=None,unit_ids=None,start_frame=0,end_frame=None,size=(800,400)):
        vd.Component.__init__(self)

        vd.devel.loadBootstrap()
        vd.devel.loadCss(url='https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css')
        vd.devel.loadJavascript(path=source_path+'/mda.js')
        vd.devel.loadJavascript(path=source_path+'/timeseriesmodel.js')
        vd.devel.loadJavascript(path=source_path+'/canvaswidget.js')
        vd.devel.loadJavascript(path=source_path+'/timeserieswidget.js')
        vd.devel.loadJavascript(path=source_path+'/../dist/jquery-3.3.1.min.js')

        self._array=recording.getTraces()
        self._array_b64=_mda32_to_base64(self._array)
        self._div_id='SFTimeseriesWidget-'+str(uuid.uuid4())
        self._recording=recording

        if sorting:
            self._sorting=sorting
            if not unit_ids:
                unit_ids = sorting.getUnitIds()
            # This is not ideal as it seems possible to get this information directly from the recording
            # Alas we cannot be sure this recording (as opposed to it's parent) was the one used for sorting
            if not end_frame:
                end_frame = len(self._array[0])
            spike_trains_str = ['[{}]'.format(','.join(str(x) for x in
                sorting.getUnitSpikeTrain(u, start_frame=start_frame, end_frame=end_frame)))
                for u in unit_ids]
            spike_trains_str = '['+','.join(spike_trains_str)+']'
        else:
            spike_trains_str ='[[]]'

        js_lines=[
                "window.sfdata=window.sfdata||{}",
                "window.sfdata.test=1",
                "window.sfdata['array_b64_{div_id}']='{b64}'".format(div_id=self._div_id,
                    b64=self._array_b64),
                "window.sfdata['spike_times']={}".format(spike_trains_str)
                    ]
        js = ";".join(js_lines)
        print(self._array.shape)
        print('length of b64: {}'.format(len(self._array_b64)))
        vd.devel.loadJavascript(js=js)
        self._size=size
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
        console.log('testing 111b');
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
        console.log(X)
        let A=new window.Mda();
        console.log(A.N1(), A.N2())
        A.setFromArrayBuffer(X);
        let TS=new window.TimeseriesModel(A);
        W.setTimeseriesModel(TS);
        W.setMarkers(window.sfdata['spike_times']);
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

import uuid
import vdomr as vd
import os
import json

source_path=os.path.dirname(os.path.realpath(__file__))

class ElectrodeGeometryWidget(vd.Component):
    def __init__(self,*,recording):
        vd.Component.__init__(self)
        self._recording=recording
        self._div_id='ElectrodeGeometryWidget-'+str(uuid.uuid4())

        vd.devel.loadBootstrap()
        vd.devel.loadCss(url='https://stackpath.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css')
        vd.devel.loadJavascript(path=source_path+'/dist/main.js')
        vd.devel.loadJavascript(path=source_path+'/dist/d3.v5.min.js')
        vd.devel.loadJavascript(path=source_path+'/dist/jquery-3.3.1.min.js')

        js="window.sfdata=window.sfdata||{}; window.sfdata['electrode_geometry_{div_id}']={obj}"
        js=self._div_id.join(js.split('{div_id}'))
        obj=self._get_geom()
        js=json.dumps(obj).join(js.split('{obj}'))
        vd.devel.loadJavascript(js=js)
    def _get_geom(self):
        RX=self._recording
        electrodes=[]
        for ch in RX.getChannelIds():
            location=RX.getChannelProperty(channel_id=ch,property_name='location')
            electrodes.append(
                dict(
                    channel_id=ch,
                    location=list(location)
                )
            )
        obj=dict(electrodes=electrodes)
        return obj
    def render(self):
        div=vd.div(id=self._div_id)
        js="""
        let W=new window.GeomWidget();
        let X=window.sfdata['electrode_geometry_{z_id}']
        console.log(X);
        W.setGeometry(X);
        //W.setSize(300,300)
        $('#{div_id}').empty();
        $('#{div_id}').append(W.div());
        W.update();
        """
        js=self._div_id.join(js.split('{div_id}'))
        vd.devel.loadJavascript(js=js,delay=1)
        return div
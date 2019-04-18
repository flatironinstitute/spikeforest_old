import uuid
from spikeforest import mdaio
import io
import base64
import vdomr as vd
import os
import numpy as np
import mlprocessors as mlpr
from spikeforest import SFMdaRecordingExtractor
from mountaintools import client as mt
import spikeextractors as se
from spikeforest import EfficientAccessRecordingExtractor
import mtlogging
import time

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

        self._div_id='SFTimeseriesWidget-'+str(uuid.uuid4())
        self._recording = recording
        self._multiscale_recordings = _create_multiscale_recordings(recording=recording, progressive_ds_factor=3)
        self._segment_size = 1000
        self._data_segments_set = dict()

        if sorting:
            self._sorting=sorting
            if not unit_ids:
                unit_ids = sorting.getUnitIds()
            # This is not ideal as it seems possible to get this information directly from the recording
            # Alas we cannot be sure this recording (as opposed to it's parent) was the one used for sorting
            if not end_frame:
                end_frame = len(recording.getNumFrames())
            spike_trains_list = ['[{}]'.format(','.join(str(x) for x in
                sorting.getUnitSpikeTrain(u, start_frame=start_frame, end_frame=end_frame)))
                for u in unit_ids]
            spike_trains_str = '['+','.join(spike_trains_str)+']'
        else:
            spike_trains_str ='[[]]'

        # js_lines=[
        #         "window.sfdata=window.sfdata||{}",
        #         "window.sfdata.test=1",
        #         "window.sfdata['array_b64_{div_id}']='{b64}'".format(div_id=self._div_id,
        #             b64=self._array_b64),
        #         "window.sfdata['spike_times']={}".format(spike_trains_str)
        #             ]
        # js = ";".join(js_lines)
        # vd.devel.loadJavascript(js=js)

        # important to set some data here so that the auto-scaling can take place
        self._set_data_segment(ds_factor=1, segment_num=0, autoscale=True)

        self._size=size

    @mtlogging.log()
    def _set_data_segment(self, *, ds_factor, segment_num, autoscale=False):
        code0 = '{}-{}'.format(int(ds_factor), int(segment_num))
        if code0 in self._data_segments_set:
            return

        ds_factor = int(ds_factor)
        self._data_segments_set[code0] = True

        # X = _compute_data_segment(recording=self._recording, ds_factor=ds_factor, segment_num=segment_num, segment_size=self._segment_size)
        if ds_factor == 1:
            X = _extract_data_segment(recording=self._recording, segment_num=segment_num, segment_size=self._segment_size)
        else:
            rx = self._multiscale_recordings[ds_factor]
            X = _extract_data_segment(recording=rx, segment_num=segment_num, segment_size=self._segment_size*2)

        # X = ComputeDataSegment.execute(
        #     recording=self._recording,
        #     ds_factor=ds_factor,
        #     segment_num=segment_num,
        #     segment_size=self._segment_size,
        #     array_out=True
        # ).outputs['array_out']

        X_b64=_mda32_to_base64(X)
        js = """
        let TS = window.timeseries_models['{component_id}'];
        let X=new window.Mda();
        X.setFromBase64('{X_b64}');
        TS.setDataSegment({ds_factor}, {segment_num}, X);
        """

        if autoscale:
            js = js + """
            let W = window.timeseries_widgets['{component_id}'];
            W.autoScale();
            """

        js = js.replace('{component_id}', self.componentId())
        js = js.replace('{X_b64}', X_b64)
        js = js.replace('{ds_factor}', str(ds_factor))
        js = js.replace('{segment_num}', str(segment_num))

        self.executeJavascript(js=js)
    def setSize(self,size):
        if self._size==size:
            return
        self._size=size
        self._update_size()
    def size(self):
        return self._size
    def _update_size(self):
        js = """
        let W=window.timeseries_widgets['{component_id}'];
        W.setSize({width},{height});
        $('#{div_id}').css({width:'{width}px',height:'{height}px'});
        """
        js = js.replace('{div_id}', self._div_id)
        js = js.replace('{component_id}', self.componentId())
        js = js.replace('{width}', str(self._size[0]))
        js = js.replace('{height}', str(self._size[1]))
        self.executeJavascript(js)
    def render(self):
        div=vd.div(id=self._div_id)
        self._update_size()
        return div
    def postRenderScript(self):
        js="""
        if (!window.timeseries_models) window.timeseries_models={};
        if (!window.timeseries_models['{component_id}']) {
            let TS0=new window.TimeseriesModel({samplerate:{samplerate}, num_channels:{num_channels}, num_timepoints:{num_timepoints}, segment_size:{segment_size}});
            window.timeseries_models['{component_id}'] = TS0;
        }
        let TS = window.timeseries_models['{component_id}'];

        TS.onRequestDataSegment(request_data_segment);
        
        if (!window.spike_times) window.spike_times={};
        //window.spike_times['{component_id}']={spike_trains}";

        function request_data_segment(ds_factor, num) {
            window.vdomr_invokeFunction('{request_data_segment_callback_id}', [ds_factor, num], {});
        }

        if (!window.timeseries_widgets) window.timeseries_widgets={};
        if (!window.timeseries_widgets['{component_id}']) {
            let W0=new window.TimeseriesWidget();
            W0.setSyncGroup('test');
            W0.setTimeseriesModel(TS);
            window.timeseries_widgets['{component_id}'] = W0;
        }
        let W=window.timeseries_widgets['{component_id}'];
        //W.setMarkers(window.spike_times['{component_id}']);
        $('#{div_id}').empty();
        $('#{div_id}').append(W.element());
        """

        request_data_segment_callback_id = 'request-data-segment-' + str(uuid.uuid4())
        vd.register_callback(request_data_segment_callback_id, lambda ds_factor, segment_num: self._set_data_segment(ds_factor=ds_factor, segment_num=segment_num))

        js = js.replace('{div_id}', self._div_id)
        js = js.replace('{component_id}', self.componentId())
        # js = js.replace('{spike_trains}', spike_trains_str)
        js = js.replace('{samplerate}', str(self._recording.getSamplingFrequency()))
        js = js.replace('{num_channels}', str(self._recording.getNumChannels()))
        js = js.replace('{num_timepoints}', str(self._recording.getNumFrames()))
        js = js.replace('{segment_size}', str(self._segment_size))
        js = js.replace('{request_data_segment_callback_id}', request_data_segment_callback_id)
        return js

def _do_downsample(X, ds_factor):
    M = X.shape[0]
    N = X.shape[1]
    N2 = N//ds_factor
    X_reshaped = np.reshape(X, (M, N2, ds_factor), order='C')
    ret = np.zeros((M, N2*2))
    ret[:,0::2] = np.min(X_reshaped, axis=2)
    ret[:,1::2] = np.max(X_reshaped, axis=2)
    return ret

@mtlogging.log()
def _extract_data_segment(*, recording, segment_num, segment_size):
    segment_num = int(segment_num)
    segment_size = int(segment_size)
    a1 = segment_size*segment_num
    a2 = segment_size*(segment_num+1)
    if a2>recording.getNumFrames():
        a2 = recording.getNumFrames()
    X = recording.getTraces(start_frame=a1, end_frame=a2)
    return X

# to remove
# class ComputeDataSegment(mlpr.Processor):
#     recording = mlpr.Input()
#     segment_size = mlpr.IntegerParameter()
#     segment_num = mlpr.IntegerParameter()
#     ds_factor = mlpr.IntegerParameter()
#     array_out = mlpr.OutputArray()

#     def run(self):
#         X = _compute_data_segment(
#             recording=self.recording,
#             segment_size=self.segment_size,
#             segment_num=self.segment_num,
#             ds_factor=int(self.ds_factor), # not sure why we need to cast as an int here
#         )
#         print('===================== Saving file to:', self.array_out, X.shape)
#         np.save(self.array_out, X)

def precomputeMultiscaleRecordings(*, recording):
    _create_multiscale_recordings(recording=recording, progressive_ds_factor=3)

def _create_multiscale_recordings(*, recording, progressive_ds_factor):
    ret = dict()
    current_rx = recording
    current_ds_factor = 1
    N = recording.getNumFrames()
    recording_has_minmax=False
    while current_ds_factor*progressive_ds_factor < N:
        current_rx = _DownsampledRecordingExtractor(recording=current_rx, ds_factor=progressive_ds_factor, input_has_minmax=recording_has_minmax)
        current_rx = EfficientAccessRecordingExtractor(recording=current_rx)
        current_ds_factor = current_ds_factor*progressive_ds_factor
        ret[current_ds_factor] = current_rx
        recording_has_minmax = True
    return ret

class _DownsampledRecordingExtractor(se.RecordingExtractor):
    def __init__(self, *, recording, ds_factor, input_has_minmax):
        se.RecordingExtractor.__init__(self)
        self._recording = recording
        self._ds_factor = ds_factor
        self._input_has_minmax = input_has_minmax
        self.copyChannelProperties(recording)
    
    def hash(self):
        return mt.sha1OfObject(dict(
            name='downsampled-recording-extractor',
            version=2,
            recording = self._recording.hash(),
            ds_factor = self._ds_factor,
            input_has_minmax = self._input_has_minmax
        ))
        
    def getChannelIds(self):
        # same channel IDs
        return self._recording.getChannelIds()

    def getNumFrames(self):
        if self._input_has_minmax:
            # number of frames is just /ds_factor (but not quite -- tricky!)
            return ((self._recording.getNumFrames() // 2) // self._ds_factor) * 2
        else:
            # need to double because we will now keep track of mins and maxs
            return (self._recording.getNumFrames() // self._ds_factor) * 2

    def getSamplingFrequency(self):
        if self._input_has_minmax:
            # sampling frequency is just /ds_factor
            return self._recording.getSamplingFrequency() / self._ds_factor
        else:
            # need to double because we will now keep track of mins and maxes
            return (self._recording.getSamplingFrequency() / self._ds_factor) * 2

    def getTraces(self, channel_ids=None, start_frame=None, end_frame=None):
        ds_factor = self._ds_factor
        if self._input_has_minmax:
            # get the traces *ds_factor
            X = self._recording.getTraces(
                channel_ids=channel_ids,
                start_frame=start_frame*ds_factor,
                end_frame=end_frame*ds_factor
            )
            X_mins = X[:,0::2] # here are the minimums
            X_maxs = X[:,1::2] # here are the maximums
            X_mins_reshaped = np.reshape(X_mins, (X_mins.shape[0], X_mins.shape[1]//ds_factor, ds_factor), order='C')
            X_maxs_reshaped = np.reshape(X_maxs, (X_maxs.shape[0], X_maxs.shape[1]//ds_factor, ds_factor), order='C')
            # the size of the output is the size X divided by ds_factor
            ret = np.zeros((X.shape[0], X.shape[1]//ds_factor))
            ret[:,0::2] = np.min(X_mins_reshaped, axis=2) # here are the mins
            ret[:,1::2] = np.max(X_maxs_reshaped, axis=2) # here are the maxs
            return ret
        else:
            X = self._recording.getTraces(
                channel_ids=channel_ids,
                start_frame=start_frame*self._ds_factor//2,
                end_frame=end_frame*self._ds_factor//2
            )
            X_reshaped = np.reshape(X, (X.shape[0], X.shape[1]//ds_factor, ds_factor), order='C')
            ret = np.zeros((X.shape[0], (X.shape[1]//ds_factor)*2))
            ret[:,0::2] = np.min(X_reshaped, axis=2)
            ret[:,1::2] = np.max(X_reshaped, axis=2)
            return ret
    
    @staticmethod
    def writeRecording(recording, save_path):
        rx = EfficientAccessRecordingExtractor(recording=recording, _dest_path=save_path)

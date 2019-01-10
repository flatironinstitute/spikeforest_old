import spikeextractors as se
import spiketoolkit as st
import vdomr as vd
import spikewidgets as sw
import spikeforestwidgets as SFW
import mlprocessors as mlpr
from matplotlib import pyplot as plt
from PIL import Image
import os
import base64
import uuid
from kbucket import client as kb

class ScrollArea(vd.Component):
  def __init__(self,child,*,height):
    vd.Component.__init__(self)
    self._child=child
    self._height=height
  def render(self):
    return vd.div(self._child,style=dict(overflow='auto',height='{}px'.format(self._height)))

class ImageView(vd.Component):
    def __init__(self,fname):
        vd.Component.__init__(self)
        with open(fname,'rb') as f:
            self._data_b64=base64.b64encode(f.read()).decode('utf-8')
        self._elmt_id='ImageView-'+str(uuid.uuid4())
    def render(self):
        elmt=vd.img(id=self._elmt_id)
        js="""
        document.getElementById('{elmt_id}').src='data:image/jpeg;base64, {data_b64}';
        """
        js=self._elmt_id.join(js.split('{elmt_id}'))
        js=self._data_b64.join(js.split('{data_b64}'))
        vd.devel.loadJavascript(js=js,delay=1)
        return elmt

class TrueUnitsWidget(vd.Component):
    def __init__(self,*,true_units_info):
        vd.Component.__init__(self)
        self._true_units_info=true_units_info
    def render(self):
        rows=[]
        rows.append(vd.tr(
            vd.th('Unit ID'),
            vd.th('SNR'),
            vd.th('Peak channel'),
            vd.th('Num. events'),
            vd.th('Firing rate')
        ))
        for unit in self._true_units_info:
            rows.append(vd.tr(
                vd.td(str(unit['unit_id'])),
                vd.td(str(unit['snr'])),
                vd.td(str(unit['peak_channel'])),
                vd.td(str(unit['num_events'])),
                vd.td(str(unit['firing_rate']))
            ))
        table=vd.table(rows,class_='table')
        return vd.div(ScrollArea(vd.div(table),height=400))

class PlotUnitWaveforms(mlpr.Processor):
    VERSION='0.1.0'
    recording_dir=mlpr.Input(directory=True,description='Recording directory')
    channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
    firings=mlpr.Input('Firings file (sorting)')
    plot_out=mlpr.Output('Plot as .jpg image file')
    
    def run(self):
        recording=se.MdaRecordingExtractor(dataset_directory=self.recording_dir)
        if len(self.channels)>0:
            recording=se.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
        sorting=se.MdaSortingExtractor(firings_file=self.firings)
        sw.UnitWaveformsWidget(recording=recording,sorting=sorting).plot()
        fname=save_plot(self.plot_out)

class PlotAutoCorrelograms(mlpr.Processor):
    NAME='spikeforest.PlotAutoCorrelograms'
    VERSION='0.1.0'
    recording_dir=mlpr.Input(directory=True,description='Recording directory')
    channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
    firings=mlpr.Input('Firings file (sorting)')
    plot_out=mlpr.Output('Plot as .jpg image file')
    
    def run(self):
        recording=se.MdaRecordingExtractor(dataset_directory=self.recording_dir,download=False)
        if len(self.channels)>0:
            recording=se.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
        sorting=se.MdaSortingExtractor(firings_file=self.firings)
        sw.CrossCorrelogramsWidget(samplerate=recording.getSamplingFrequency(),sorting=sorting).plot()
        fname=save_plot(self.plot_out)

def save_plot(fname,quality=40):
    plt.savefig(fname+'.png')
    plt.close()
    im=Image.open(fname+'.png').convert('RGB')
    os.remove(fname+'.png')
    im.save(fname,quality=quality)

class SFRecordingWidget(vd.Component):
  def __init__(self):
    vd.Component.__init__(self)
    self._recording=None
    self._view=None
    vd.devel.loadBootstrap()
  def setRecording(self,recording):
    self._recording=recording
    self._view=None
    #self._timeseries_widget=
    self.refresh()
  def _on_view_timeseries(self):
    rx=self._recording.recordingExtractor()
    sf=rx.getSamplingFrequency()
    if self._recording.recordingFileIsLocal():
        rx=se.SubRecordingExtractor(parent_recording=rx,start_frame=int(sf*0),end_frame=int(sf*10))
    else:
        rx=se.SubRecordingExtractor(parent_recording=rx,start_frame=int(sf*0),end_frame=int(sf*1))
    rx=st.preprocessing.bandpass_filter(recording=rx,freq_min=300,freq_max=6000)
    self._view=SFW.TimeseriesWidget(recording=rx)
    self.refresh()
  def _on_view_geometry(self):
    rx=self._recording.recordingExtractor()
    self._view=SFW.ElectrodeGeometryWidget(recording=rx)
    self.refresh()
  def _on_view_true_units(self):
    info=self._recording.trueUnitsInfo(format='json')
    self._view=TrueUnitsWidget(true_units_info=info)
    self.refresh()
  def _on_view_true_unit_waveforms(self):
    rx=self._recording.recordingExtractor()
    rx=st.preprocessing.bandpass_filter(recording=rx,freq_min=300,freq_max=6000)
    sx=self._recording.sortingTrue()
    self._view=SFW.UnitWaveformsWidget(recording=rx,sorting=sx)
    self.refresh()
  def _on_view_true_unit_autocorrelograms(self):
    dirname=self._recording.directory()
    img=PlotAutoCorrelograms.execute(
      recording_dir=dirname,
      channels=[],
      firings=dirname+'/firings_true.mda',
      plot_out={'ext':'.jpg'}
    ).outputs['plot_out']
    img=kb.realizeFile(img)
    self._view=ImageView(img)
    self.refresh()
  def _on_download_recording_file(self):
    self._recording.realizeRecordingFile()
    self.refresh()
  def _on_download_firings_true_file(self):
    self._recording.realizeFiringsTrueFile()
    self.refresh()
  def render(self):
    if not self._recording:
      return vd.div('---')
    rec=self._recording
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

    recording_file_is_local=self._recording.recordingFileIsLocal()
    if recording_file_is_local:
        elmt='True'
    else:
        elmt=vd.span('False',' ',vd.a('(download)',onclick=self._on_download_recording_file))
    rows.append(vd.tr(
        vd.th('raw.mda is downloaded'),vd.td(elmt))
    )

    firings_true_file_is_local=self._recording.firingsTrueFileIsLocal()
    if firings_true_file_is_local:
        elmt='True'
    else:
        elmt=vd.span('False',' ',vd.a('(download)',onclick=self._on_download_firings_true_file))
    rows.append(vd.tr(
        vd.th('firings_true.mda is downloaded'),vd.td(elmt))
    )

    table=vd.table(rows,style={'text-align':'left','width':'auto','font-size':'13px'},class_='table')
    button_style={'margin':'3px'}
    view_timeseries_button=vd.button('View timeseries',onclick=self._on_view_timeseries,style=button_style)
    view_geometry_button=vd.button('View electrode geometry',onclick=self._on_view_geometry,style=button_style)
    view_true_units_button=vd.button('View true unit table',onclick=self._on_view_true_units,style=button_style)
    view_true_unit_waveforms_button=vd.button('View true unit waveforms',onclick=self._on_view_true_unit_waveforms,style=button_style)
    view_true_unit_autocorrelograms_button=vd.button('View true unit autocorrelograms',onclick=self._on_view_true_unit_autocorrelograms,style=button_style)
    button_bar=vd.div(
        view_timeseries_button,
        view_geometry_button,
        view_true_units_button,
        view_true_unit_waveforms_button,
        view_true_unit_autocorrelograms_button,
        style={'padding-bottom':'20px'}
    )
    elmts=[table,button_bar]
    
    if self._view:
        elmts.append(self._view)
    return vd.div(elmts)


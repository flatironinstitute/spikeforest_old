from matplotlib import pyplot as plt
from PIL import Image
import mlprocessors as mlpr
from kbucket import client as kb
import spikeextractors as si
import spikewidgets as sw
import os

def summarize_sorting(result):
    ret={'plots':{}}
    unit_waveforms=PlotUnitWaveforms.execute(
      recording_dir=result['recording_dir'],
      channels=result.get('channels',[]),
      firings=result['firings'],
      plot_out={'ext':'.jpg'}
    ).outputs['plot_out']
    unit_waveforms=kb.saveFile(unit_waveforms,basename='unit_waveforms.jpg')
    ret['plots']['unit_waveforms']=unit_waveforms

    autocorrelograms=PlotAutoCorrelograms.execute(
      recording_dir=result['recording_dir'],
      channels=result.get('channels',[]),
      firings=result['firings'],
      plot_out={'ext':'.jpg'}
    ).outputs['plot_out']
    autocorrelograms=kb.saveFile(autocorrelograms,basename='autocorrelograms.jpg')
    ret['plots']['autocorrelograms']=autocorrelograms

    return ret

class PlotUnitWaveforms(mlpr.Processor):
    VERSION='0.1.0'
    recording_dir=mlpr.Input(directory=True,description='Recording directory')
    channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
    firings=mlpr.Input('Firings file (sorting)')
    plot_out=mlpr.Output('Plot as .jpg image file')
    
    def run(self):
        recording=si.MdaRecordingExtractor(dataset_directory=self.recording_dir)
        if len(self.channels)>0:
            recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
        sorting=si.MdaSortingExtractor(firings_file=self.firings)
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
        recording=si.MdaRecordingExtractor(dataset_directory=self.recording_dir,download=False)
        if len(self.channels)>0:
            recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
        sorting=si.MdaSortingExtractor(firings_file=self.firings)
        sw.CrossCorrelogramsWidget(samplerate=recording.getSamplingFrequency(),sorting=sorting).plot()
        fname=save_plot(self.plot_out)

def save_plot(fname,quality=40):
    plt.savefig(fname+'.png')
    plt.close()
    im=Image.open(fname+'.png').convert('RGB')
    os.remove(fname+'.png')
    im.save(fname,quality=quality)
import mlprocessors as mlpr
from mountaintools import client as mt
from spikeforest import spikeextractors as si
import os
from copy import deepcopy
import mtlogging

@mtlogging.log()
def summarize_sortings(sortings,compute_resource,label=None):
    print('>>>>>> summarize sortings')
    # container='sha1://87319c2856f312ccc3187927ae899d1d67b066f9/03-20-2019/mountaintools_basic.simg'
    # jobs_autocor_plot=[]
    for sorting in sortings:
        recording_dir=sorting['recording']['directory']
        channels=sorting.get('channels',[])
        firings=sorting['firings']

        # job=PlotAutoCorrelograms.createJob(
        #     recording_dir=recording_dir,
        #     channels=channels,
        #     firings=firings,
        #     plot_out={'ext':'.jpg','upload':True},
        #     _container=container
        # )
        # jobs_autocor_plot.append(job)
    
    # all_jobs=jobs_autocor_plot
    all_jobs=[]
    label=label or 'Summarize sortings'
    mlpr.executeBatch(jobs=all_jobs,label=label,num_workers=None,compute_resource=compute_resource)
    
    print('Gathering summarized sortings...')
    summarized_sortings=[]
    for i,sorting in enumerate(sortings):
        summary=dict()
        summary['plots']=dict()

        sorting2=deepcopy(sorting)
        sorting2['summary']=summary
        summarized_sortings.append(sorting2)

    return summarized_sortings

    # TODO: restore this later -- once it becomes more efficient
    #unit_waveforms=PlotUnitWaveforms.execute(
    #  recording_dir=result['recording_dir'],
    #  channels=result.get('channels',[]),
    #  firings=result['firings'],
    #  plot_out={'ext':'.jpg','upload':True}
    #).outputs['plot_out']
    #unit_waveforms=ca.saveFile(path=unit_waveforms,basename='unit_waveforms.jpg')
    #ret['plots']['unit_waveforms']=unit_waveforms

# class PlotUnitWaveforms(mlpr.Processor):
#     VERSION='0.1.0'
#     recording_dir=mlpr.Input(directory=True,description='Recording directory')
#     channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
#     firings=mlpr.Input('Firings file (sorting)')
#     plot_out=mlpr.Output('Plot as .jpg image file')
    
#     def run(self):
#         recording=si.MdaRecordingExtractor(dataset_directory=self.recording_dir)
#         if len(self.channels)>0:
#             recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
#         sorting=si.MdaSortingExtractor(firings_file=self.firings)
#         sw.UnitWaveformsWidget(recording=recording,sorting=sorting).plot()
#         fname=save_plot(self.plot_out)

# class PlotAutoCorrelograms(mlpr.Processor):
#     NAME='spikeforest.PlotAutoCorrelograms'
#     VERSION='0.1.0'
#     recording_dir=mlpr.Input(directory=True,description='Recording directory')
#     channels=mlpr.IntegerListParameter(description='List of channels to use.',optional=True,default=[])
#     firings=mlpr.Input('Firings file (sorting)')
#     plot_out=mlpr.Output('Plot as .jpg image file')
    
#     def run(self):
#         recording=si.MdaRecordingExtractor(dataset_directory=self.recording_dir,download=False)
#         if len(self.channels)>0:
#             recording=si.SubRecordingExtractor(parent_recording=recording,channel_ids=self.channels)
#         sorting=si.MdaSortingExtractor(firings_file=self.firings)
#         sw.CrossCorrelogramsWidget(samplerate=recording.getSamplingFrequency(),sorting=sorting).plot()
#         fname=save_plot(self.plot_out)

# def save_plot(fname,quality=40):
#     plt.savefig(fname+'.png')
#     plt.close()
#     im=Image.open(fname+'.png').convert('RGB')
#     os.remove(fname+'.png')
#     im.save(fname,quality=quality)

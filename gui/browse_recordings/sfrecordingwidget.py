import spikeextractors as se
from spikeforest import spiketoolkit as st
import vdomr as vd
from spikeforest import spikewidgets as sw
import mlprocessors as mlpr
from matplotlib import pyplot as plt
from PIL import Image
import os
import base64
import uuid
from mountaintools import client as mt
import spikeforestwidgets as SFW
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor


class ScrollArea(vd.Component):
    def __init__(self, child, *, height):
        vd.Component.__init__(self)
        self._child = child
        self._height = height

    def render(self):
        return vd.div(self._child, style=dict(overflow='auto', height='{}px'.format(self._height)))


class ImageView(vd.Component):
    def __init__(self, fname):
        vd.Component.__init__(self)
        with open(fname, 'rb') as f:
            self._data_b64 = base64.b64encode(f.read()).decode('utf-8')
        self._elmt_id = 'ImageView-'+str(uuid.uuid4())

    def render(self):
        elmt = vd.img(id=self._elmt_id)
        js = """
        document.getElementById('{elmt_id}').src='data:image/jpeg;base64, {data_b64}';
        """
        js = self._elmt_id.join(js.split('{elmt_id}'))
        js = self._data_b64.join(js.split('{data_b64}'))
        vd.devel.loadJavascript(js=js, delay=1)
        return elmt


class TrueUnitsTable(vd.Component):
    def __init__(self, *, true_units_info):
        vd.Component.__init__(self)
        self._true_units_info = true_units_info

    def render(self):
        rows = []
        rows.append(vd.tr(
            vd.th('Unit ID'),
            vd.th('SNR'),
            vd.th('Peak channel'),
            vd.th('Num. events'),
            vd.th('Firing rate')
        ))
        if self._true_units_info:
            for unit in self._true_units_info:
                rows.append(vd.tr(
                    vd.td(str(unit['unit_id'])),
                    vd.td(str(unit['snr'])),
                    vd.td(str(unit['peak_channel'])),
                    vd.td(str(unit['num_events'])),
                    vd.td(str(unit['firing_rate']))
                ))
        else:
            print('WARNING: true units info not found.')
        table = vd.table(rows, class_='table')
        return vd.div(ScrollArea(vd.div(table), height=400))


class ComparisonWithTruthTable(vd.Component):
    def __init__(self, comparison_info):
        vd.Component.__init__(self)
        self._comparison_info = comparison_info

    def render(self):
        rows = []
        rows.append(vd.tr(
            vd.th('Unit ID'),
            vd.th('Accuracy'),
            vd.th('Best unit'),
            vd.th('Matched unit'),
            vd.th('Num. matches'),
            vd.th('False negative rate'),
            vd.th('False positive rate')
        ))
        for ii in self._comparison_info:
            unit = self._comparison_info[ii]
            rows.append(vd.tr(
                vd.td(str(unit['unit_id'])),
                vd.td(str(unit['accuracy'])),
                vd.td(str(unit['best_unit'])),
                vd.td(str(unit['matched_unit'])),
                vd.td(str(unit['num_matches'])),
                vd.td(str(unit['f_n'])),
                vd.td(str(unit['f_p']))
            ))
        table = vd.table(rows, class_='table')
        return vd.div(ScrollArea(vd.div(table), height=400))


class PlotUnitWaveforms(mlpr.Processor):
    VERSION = '0.1.0'
    recording_dir = mlpr.Input(
        directory=True, description='Recording directory')
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings = mlpr.Input('Firings file (sorting)')
    plot_out = mlpr.Output('Plot as .jpg image file')

    def run(self):
        recording = SFMdaRecordingExtractor(
            dataset_directory=self.recording_dir)
        if len(self.channels) > 0:
            recording = se.SubRecordingExtractor(
                parent_recording=recording, channel_ids=self.channels)
        sorting = SFMdaSortingExtractor(firings_file=self.firings)
        sw.UnitWaveformsWidget(recording=recording, sorting=sorting).plot()
        save_plot(self.plot_out)


class PlotAutoCorrelograms(mlpr.Processor):
    NAME = 'spikeforest.PlotAutoCorrelograms'
    VERSION = '0.1.0'
    recording_dir = mlpr.Input(
        directory=True, description='Recording directory')
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings = mlpr.Input('Firings file (sorting)')
    plot_out = mlpr.Output('Plot as .jpg image file')

    def run(self):
        recording = SFMdaRecordingExtractor(
            dataset_directory=self.recording_dir, download=False)
        if len(self.channels) > 0:
            recording = se.SubRecordingExtractor(
                parent_recording=recording, channel_ids=self.channels)
        sorting = SFMdaSortingExtractor(firings_file=self.firings)
        sw.CrossCorrelogramsWidget(
            samplerate=recording.getSamplingFrequency(), sorting=sorting).plot()
        save_plot(self.plot_out)


def save_plot(fname, quality=40):
    plt.savefig(fname+'.png')
    plt.close()
    im = Image.open(fname+'.png').convert('RGB')
    os.remove(fname+'.png')
    im.save(fname, quality=quality)


class ButtonBar(vd.Component):
    def __init__(self, data):
        vd.Component.__init__(self)
        self._data = data

    def render(self):
        button_style = {'margin': '3px'}
        buttons = [
            vd.button(item[0], onclick=item[1], style=button_style)
            for item in self._data
        ]
        return vd.div(buttons, style={'padding-bottom': '20px'})


class SFRecordingWidget(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._recording = None
        self._sorting_result_name = None
        self._view = None
        vd.devel.loadBootstrap()

    def setRecording(self, recording):
        self._recording = recording
        self._view = None
        # self._timeseries_widget=
        self.refresh()

    def setSortingResultName(self, name):
        self._sorting_result_name = name
        self.refresh()

    def _on_view_timeseries(self):
        rx = self._recording.recordingExtractor()
        sf = rx.getSamplingFrequency()
        if self._recording.recordingFileIsLocal():
            rx = se.SubRecordingExtractor(
                parent_recording=rx, start_frame=int(sf*0), end_frame=int(sf*10))
        else:
            rx = se.SubRecordingExtractor(
                parent_recording=rx, start_frame=int(sf*0), end_frame=int(sf*1))
        rx = st.preprocessing.bandpass_filter(
            recording=rx, freq_min=300, freq_max=6000)
        self._view = SFW.TimeseriesWidget(recording=rx)
        self.refresh()

    def _on_view_geometry(self):
        rx = self._recording.recordingExtractor()
        self._view = SFW.ElectrodeGeometryWidget(recording=rx)
        self.refresh()

    def _on_view_true_units(self):
        info = self._recording.trueUnitsInfo(format='json')
        print(info)
        self._view = TrueUnitsTable(true_units_info=info)
        self.refresh()

    def _on_view_true_unit_waveforms(self):
        rx = self._recording.recordingExtractor()
        rx = st.preprocessing.bandpass_filter(
            recording=rx, freq_min=300, freq_max=6000)
        sx = self._recording.sortingTrue()
        self._view = SFW.UnitWaveformsWidget(recording=rx, sorting=sx)
        self.refresh()

    def _on_view_true_unit_autocorrelograms(self):
        dirname = self._recording.directory()
        img = PlotAutoCorrelograms.execute(
            recording_dir=dirname,
            channels=[],
            firings=dirname+'/firings_true.mda',
            plot_out={'ext': '.jpg'}
        ).outputs['plot_out']
        img = mt.realizeFile(img)
        self._view = ImageView(img)
        self.refresh()

    def _on_download_recording_file(self):
        self._recording.realizeRecordingFile()
        self.refresh()

    def _on_download_firings_true_file(self):
        self._recording.realizeFiringsTrueFile()
        self.refresh()

    def _on_view_comparison_with_truth_table(self):
        res = self._recording.sortingResult(self._sorting_result_name)
        info = res.comparisonWithTruth(format='json')
        self._view = ComparisonWithTruthTable(info)
        self.refresh()

    def _on_view_sorted_unit_waveforms(self):
        rx = self._recording.recordingExtractor()
        rx = st.preprocessing.bandpass_filter(
            recording=rx, freq_min=300, freq_max=6000)
        res = self._recording.sortingResult(self._sorting_result_name)
        sx = res.sorting()
        self._view = SFW.UnitWaveformsWidget(recording=rx, sorting=sx)
        self.refresh()

    def render(self):
        if not self._recording:
            return vd.div('___')
        rec = self._recording
        rows = []
        rows.append(vd.tr(
            vd.th('Study'), vd.td(rec.study().name())
        ))
        rows.append(vd.tr(
            vd.th('Recording'), vd.td(rec.name())
        ))
        rows.append(vd.tr(
            vd.th('Directory'), vd.td(rec.directory())
        ))
        true_units = rec.trueUnitsInfo(format='json')
        if true_units:
            rows.append(vd.tr(
                vd.th('Num. true units'), vd.td('{}'.format(len(true_units)))
            ))
        RX = rec.recordingExtractor()
        rows.append(vd.tr(
            vd.th('Num. channels'), vd.td('{}'.format(len(RX.getChannelIds())))
        ))
        rows.append(vd.tr(
            vd.th('Samplerate'), vd.td('{}'.format(RX.getSamplingFrequency()))
        ))
        a = RX.getNumFrames() / RX.getSamplingFrequency()
        rows.append(vd.tr(            
            vd.th('Duration (s)'), vd.td('{}'.format(a))
        ))        

        recording_file_is_local = self._recording.recordingFileIsLocal()
        if recording_file_is_local:
            elmt = 'True'
        else:
            elmt = vd.span('False', ' ', vd.a(
                '(download)', onclick=self._on_download_recording_file))
        rows.append(vd.tr(
            vd.th('raw.mda is downloaded'), vd.td(elmt))
        )

        firings_true_file_is_local = self._recording.firingsTrueFileIsLocal()
        if firings_true_file_is_local:
            elmt = 'True'
        else:
            elmt = vd.span('False', ' ', vd.a(
                '(download)', onclick=self._on_download_firings_true_file))
        rows.append(vd.tr(
            vd.th('firings_true.mda is downloaded'), vd.td(elmt))
        )

        res = None
        if self._sorting_result_name:
            res = self._recording.sortingResult(self._sorting_result_name)

        if res:
            rows.append(vd.tr(
                vd.th('Sorting result'), vd.td(self._sorting_result_name)
            ))
            sorting = res.sorting()
            rows.append(vd.tr(
                vd.th('Num. sorted units'), vd.td(
                    '{}'.format(len(sorting.getUnitIds())))
            ))

        table = vd.table(rows, style={
                         'text-align': 'left', 'width': 'auto', 'font-size': '13px'}, class_='table')

        button_bar = ButtonBar([
            ('View timeseries', self._on_view_timeseries),
            ('View electrode geometry', self._on_view_geometry),
            ('View true unit table', self._on_view_true_units),
            ('View true unit waveforms', self._on_view_true_unit_waveforms),
            ('View true unit autocorrelograms',
             self._on_view_true_unit_autocorrelograms)
        ])
        elmts = [table, button_bar]

        if res:
            button_bar_result = ButtonBar([
                ('View comparison with truth table',
                 self._on_view_comparison_with_truth_table),
                ('View sorted unit waveforms', self._on_view_sorted_unit_waveforms)
            ])
            elmts.append(button_bar_result)

        if self._view:
            elmts.append(self._view)

        return vd.div(elmts)
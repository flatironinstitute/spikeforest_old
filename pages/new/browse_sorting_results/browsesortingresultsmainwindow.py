import os
import vdomr as vd
import spikeforest as sf
from kbucket import client as kb
import spikeforestwidgets as SFW
from sortingresultexplorer import SortingResultExplorer
os.environ['SIMPLOT_SRC_DIR'] = '../../simplot'


class SortingResultSelectWidget(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)

        self._SEL_group = vd.components.SelectBox(options=[])
        self._SEL_group.onChange(self._on_group_changed)
        self._SEL_study = vd.components.SelectBox(options=[])
        self._SEL_study.onChange(self._on_study_changed)
        self._SEL_recording = vd.components.SelectBox(options=[])
        self._SEL_recording.onChange(self._on_recording_changed)
        self._SEL_sorting_result = vd.components.SelectBox(options=[])
        self._SEL_sorting_result.onChange(self._on_sorting_result_changed)
        self._selection_changed_handlers = []

        vd.devel.loadBootstrap()

    def initialize(self):
        self._group_names = kb.loadObject(
            key=dict(name='spikeforest_recording_group_names')
        )
        self._sorter_names = kb.loadObject(
            key=dict(name='spikeforest_sorter_names')
        )
        self._SEL_group.setOptions(['']+self._group_names)
        self._SEL_group.setValue('magland_synth_test')
        self._on_group_changed(value=self._SEL_group.value())

    def onSelectionChanged(self, handler):
        self._selection_changed_handlers.append(handler)

    def recording(self):
        study_name = self._SEL_study.value()
        recording_name = self._SEL_recording.value()

        study = self._SF.study(study_name)
        rec = study.recording(recording_name)
        return rec

    def sortingResultName(self):
        sorting_result_name = self._SEL_sorting_result.value()
        if not sorting_result_name:
            return None
        return sorting_result_name

    def _on_group_changed(self, value):
        group_name = self._SEL_group.value()
        if not group_name:
            return
        a = kb.loadObject(
            key=dict(name='summarized_recordings', group_name=group_name)
        )
        if not a:
            print('ERROR: unable to open recording group: '+group_name)
            return

        if ('recordings' not in a) or ('studies' not in a):
            print('ERROR: problem with recording group: '+group_name)
            return

        studies = a['studies']
        recordings = a['recordings']

        SF = sf.SFData()
        SF.loadStudies(studies)
        SF.loadRecordings2(recordings)

        sorter_names = self._sorter_names[group_name]
        for sorter_name in sorter_names:
            print('Loading sorting results for sorter: '+sorter_name)
            b = kb.loadObject(
                key=dict(name='sorting_results',
                         group_name=group_name, sorter_name=sorter_name)
            )
            if not b:
                print('WARNING: unable to open sorting results for sorter: '+sorter_name)
                break
            SF.loadSortingResults(b['sorting_results'])

        self._SF = SF
        self._SEL_study.setOptions(SF.studyNames())
        self._on_study_changed(value=self._SEL_study.value())

    def _on_study_changed(self, value):
        if not self._SF:
            return
        study_name = self._SEL_study.value()
        if not study_name:
            self._SEL_recording.setOptions([])
            return
        study = self._SF.study(study_name)
        self._SEL_recording.setOptions(study.recordingNames())
        self._on_recording_changed(value=self._SEL_recording.value())

    def _on_recording_changed(self, value):
        rec = self.recording()
        srnames = rec.sortingResultNames()
        # opts = ['']+srnames
        opts = srnames
        self._SEL_sorting_result.setOptions(opts)
        self._on_sorting_result_changed(value=self._SEL_sorting_result.value())

    def _on_sorting_result_changed(self, value):
        for handler in self._selection_changed_handlers:
            handler()
        pass

    def render(self):
        rows = [
            vd.tr(vd.td('Select a group:'), vd.td(self._SEL_group)),
            vd.tr(vd.td('Select a study:'), vd.td(self._SEL_study)),
            vd.tr(vd.td('Select a recording:'), vd.td(self._SEL_recording)),
            vd.tr(vd.td('Select a sorting result:'),
                  vd.td(self._SEL_sorting_result))
        ]
        select_table = vd.table(
            rows, style={'text-align': 'left', 'width': 'auto'}, class_='table')
        return vd.div(
            select_table
        )


class BrowseSortingResultsMainWindow(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._select_widget = SortingResultSelectWidget()
        self._explorer = None

        self._select_widget.onSelectionChanged(self._on_selection_changed)
        self._select_widget.initialize()

    def _on_selection_changed(self):
        rec = self._select_widget.recording()
        if not rec:
            return
        sorting_result_name = self._select_widget.sortingResultName()
        if not sorting_result_name:
            return
        res = rec.sortingResult(sorting_result_name)
        self._explorer = SortingResultExplorer(sorting_result=res)
        self.refresh()

    def render(self):
        list = [self._select_widget]
        if self._explorer:
            list.append(self._explorer)
        return vd.div(
            list
        )

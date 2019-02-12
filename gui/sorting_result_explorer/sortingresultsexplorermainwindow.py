import os
import vdomr as vd
import spikeforest as sf
from cairio import client as ca
import spikeforestwidgets as SFW
from sortingresultexplorer import SortingResultExplorer
os.environ['SIMPLOT_SRC_DIR'] = '../../simplot'


class SortingResultSelectWidget(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)

        self._SEL_output_id = vd.components.SelectBox(options=[])
        self._SEL_output_id.onChange(self._on_output_id_changed)
        self._SEL_study = vd.components.SelectBox(options=[])
        self._SEL_study.onChange(self._on_study_changed)
        self._SEL_recording = vd.components.SelectBox(options=[])
        self._SEL_recording.onChange(self._on_recording_changed)
        self._SEL_sorting_result = vd.components.SelectBox(options=[])
        self._SEL_sorting_result.onChange(self._on_sorting_result_changed)
        self._selection_changed_handlers = []

        vd.devel.loadBootstrap()

    def initialize(self):
        self._output_ids = ['spikeforest_test0','spikeforest_test1']
        #kb.loadObject(
        #    key=dict(name='spikeforest_batch_group_names'))
        self._SEL_output_id.setOptions(['']+self._output_ids)
        self._on_output_id_changed(value=self._SEL_output_id.value())

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

    def _on_output_id_changed(self, value):
        output_id = self._SEL_output_id.value()
        if not output_id:
            return
        key=dict(
            name='spikeforest_results',
            output_id=output_id
        )
        a = ca.loadObject(key=key)
        if a is None:
            raise Exception('Unable to load spikeforest result: {}'.format(output_id))
        SF = sf.SFData()
        SF.loadStudies(a['studies'])
        SF.loadRecordings2(a['recordings'])
        SF.loadSortingResults(a['sorting_results'])
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
            vd.tr(vd.td('Select an output id:'), vd.td(self._SEL_output_id)),
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


class SortingResultsExplorerMainWindow(vd.Component):
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

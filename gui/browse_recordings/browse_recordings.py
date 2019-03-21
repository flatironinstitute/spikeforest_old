import os
import vdomr as vd
import sfdata as sf
from mountaintools import client as mt
#import spikeforestwidgets as SFW
from sfrecordingwidget import SFRecordingWidget


class MainWindow(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._recording_group_names = mt.loadObject(
            key=dict(name='spikeforest_recording_group_names'))
        self._SEL_group = vd.components.SelectBox(
            options=['']+self._recording_group_names)
        self._SEL_group.onChange(self._on_group_changed)
        self._SEL_study = vd.components.SelectBox(options=[])
        self._SEL_study.onChange(self._on_study_changed)
        self._SEL_recording = vd.components.SelectBox(options=[])
        self._SEL_recording.onChange(self._on_recording_changed)
        self._recording_widget = SFRecordingWidget()

        self._on_group_changed(value=self._SEL_group.value())

        vd.devel.loadBootstrap()

    def _on_group_changed(self, value):
        group_name = self._SEL_group.value()
        if not group_name:
            return
        a = mt.loadObject(
            key=dict(name='spikeforest_recording_group', group_name=group_name))
        # key=dict(name='spikeforest_results', output_id='spikeforest_test2'))
        SF = sf.SFData()
        SF.loadStudies(a['studies'])
        SF.loadRecordings2(a['recordings'])
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
        study_name = self._SEL_study.value()
        recording_name = self._SEL_recording.value()

        if (not study_name) or (not recording_name):
            self._recording_widget.setRecording(None)
            return

        study = self._SF.study(study_name)
        rec = study.recording(recording_name)
        self._recording_widget.setRecording(rec)

    def render(self):
        rows = [
            vd.tr(vd.td('Select a group:'), vd.td(self._SEL_group)),
            vd.tr(vd.td('Select a study:'), vd.td(self._SEL_study)),
            vd.tr(vd.td('Select a recording:'), vd.td(self._SEL_recording))
        ]
        select_table = vd.table(
            rows, style={'text-align': 'left', 'width': 'auto'}, class_='table')
        return vd.div(
            select_table,
            self._recording_widget
        )


class TheApp():
    def __init__(self):
        pass

    def createSession(self):
        W = MainWindow()
        return W


def main():
    # Configure readonly access to kbucket
    mt.autoConfig(collection='spikeforest', key='spikeforest2-readonly')

    APP = TheApp()
    server = vd.VDOMRServer(APP)
    server.start()
    # W=MainWindow()
    #vd.pywebview_start(root=W,title='Browse Recordings')


if __name__ == "__main__":
    main()

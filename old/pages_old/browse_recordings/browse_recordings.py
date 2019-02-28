import os
import vdomr as vd
import sfdata as sf
from kbucket import client as kb
import spikeforestwidgets as SFW


class MainWindow(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._groups = kb.loadObject(
            key=dict(name='spikeforest_batch_group_names'))
        self._SEL_group = vd.components.SelectBox(
            options=self._groups['batch_group_names'])
        self._SEL_group.onChange(self._on_group_changed)
        self._SEL_study = vd.components.SelectBox(options=[])
        self._SEL_study.onChange(self._on_study_changed)
        self._SEL_recording = vd.components.SelectBox(options=[])
        self._SEL_recording.onChange(self._on_recording_changed)
        self._recording_widget = SFW.SFRecordingWidget()

        self._on_group_changed(value=self._SEL_group.value())

        vd.devel.loadBootstrap()

    def _on_group_changed(self, value):
        group_name = self._SEL_group.value()
        a = kb.loadObject(
            key=dict(name='spikeforest_batch_group', group_name=group_name))
        SF = sf.SFData()
        for recordings_name in a['recordings_names']:
            try:
                SF.loadRecordings(key=dict(name=recordings_name))
            except:
                print('Warning: unable to load recordings: '+recordings_name)
        for batch_name in a['batch_names']:
            try:
                SF.loadProcessingBatch(batch_name=batch_name)
            except:
                print('Warning: unable to load processing batch: '+batch_name)
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
        print('creating main window')
        W = MainWindow()
        print('done creating main window')
        return W


def main():
    # Configure readonly access to kbucket
    if os.environ.get('SPIKEFOREST_PASSWORD', None):
        print('Configuring kbucket as readwrite')
        sf.kbucketConfigRemote(name='spikeforest1-readwrite',
                               password=os.environ.get('SPIKEFOREST_PASSWORD'))
    else:
        print('Configuring kbucket as readonly')
        sf.kbucketConfigRemote(name='spikeforest1-readonly')

    APP = TheApp()
    server = vd.VDOMRServer(APP)
    server.start()


if __name__ == "__main__":
    main()

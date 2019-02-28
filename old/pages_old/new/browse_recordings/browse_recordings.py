import os
import vdomr as vd
import sfdata as sf
from kbucket import client as kb
import spikeforestwidgets as SFW


class MainWindow(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._group_names = kb.loadObject(
            key=dict(name='spikeforest_recording_group_names')
        )
        self._CB_use_summarized_recordings = CheckBox(
            label='Use summarized recordings', checked=True)
        self._CB_use_summarized_recordings.onChange(self._on_group_changed)
        self._SEL_group = vd.components.SelectBox(
            options=['']+self._group_names)
        self._SEL_group.onChange(self._on_group_changed)
        self._SEL_study = vd.components.SelectBox(options=[])
        self._SEL_study.onChange(self._on_study_changed)
        self._SEL_recording = vd.components.SelectBox(options=[])
        self._SEL_recording.onChange(self._on_recording_changed)
        self._recording_widget = SFW.SFRecordingWidget()

        self._on_group_changed(value=self._SEL_group.value())

        vd.devel.loadBootstrap()

    def _on_group_changed(self, value=None):
        group_name = self._SEL_group.value()
        if not group_name:
            return
        if self._CB_use_summarized_recordings.checked():
            a = kb.loadObject(
                key=dict(name='summarized_recordings', group_name=group_name)
            )
        else:
            a = kb.loadObject(
                key=dict(name='spikeforest_recording_group',
                         group_name=group_name)
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
            self._CB_use_summarized_recordings,
            select_table,
            self._recording_widget
        )


class CheckBox(vd.Component):
    def __init__(self, checked=False, onchange=None, label='', **kwargs):
        vd.Component.__init__(self)
        self._kwargs = kwargs
        self._checked = checked
        self._label = label
        self._on_change_handlers = []
        if onchange:
            self._on_change_handlers.append(onchange)

    def checked(self):
        return self._checked

    def setChecked(self, val):
        self._checked = val
        self.refresh()

    def onChange(self, handler):
        self._on_change_handlers.append(handler)

    def _onchange(self, value):  # somehow the value is useless here, so we just toggle
        self._checked = (not self._checked)
        for handler in self._on_change_handlers:
            handler()

    def render(self):
        attrs = dict()
        if self._checked:
            attrs['checked'] = 'checked'
        X = vd.span(
            vd.input(type='checkbox', **attrs,
                     onchange=self._onchange, **self._kwargs),
            vd.span(self._label)
        )
        return X


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

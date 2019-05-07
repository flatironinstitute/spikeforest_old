#!/usr/bin/env python

import argparse
import os
import vdomr as vd
from mountaintools import client as mt
import spikeforestwidgets as SFW
import spikeextractors as se
from spikeforest import SFMdaRecordingExtractor
import uuid

class TheApp():
    def __init__(self, recording_directory):
        self._recording_directory = recording_directory

    def createSession(self):
        recording = SFMdaRecordingExtractor(
            dataset_directory=self._recording_directory, download=False)
        recording = se.SubRecordingExtractor(
            parent_recording=recording, start_frame=0, end_frame=10000)
        recording = se.NumpyRecordingExtractor(
            timeseries=recording.get_traces(), samplerate=recording.get_sampling_frequency())
        W = SFW.TimeseriesWidget(recording=recording)
        _make_full_browser(W)
        return W


def main():
    parser = argparse.ArgumentParser(description='View a ephys recording')
    parser.add_argument(
        '--port', help='The port to listen on (for a web service). Otherwise, attempt to launch as stand-alone GUI.', required=False, default=None)
    parser.add_argument('recording_directory',
                        help='The directory of the recording (on kbucket or on local system). Stored in mda format.')

    args = parser.parse_args()

    # Configure readonly access to kbucket
    # ca.autoConfig(collection='spikeforest', key='spikeforest2-readonly')

    APP = TheApp(recording_directory=args.recording_directory)

    if args.port is not None:
        vd.config_server()
        server = vd.VDOMRServer(APP)
        server.setPort(int(args.port))
        server.start()
    else:
        vd.pyqt5_start(APP=APP, title='view_timeseries')

def _make_full_browser(W):
    resize_callback_id = 'resize-callback-' + str(uuid.uuid4())
    vd.register_callback(resize_callback_id, lambda width, height: W.setSize((width, height)))
    js = """
    document.body.style="overflow:hidden";
    let onresize_scheduled=false;
    function schedule_onresize() {
        if (onresize_scheduled) return;
        onresize_scheduled=true;
        setTimeout(function() {
            onresize();
            onresize_scheduled=false;
        },100);
    }
    function onresize() {
        width = document.body.clientWidth;
        height = document.body.clientHeight;
        window.vdomr_invokeFunction('{resize_callback_id}', [width, height], {})
    }
    window.addEventListener("resize", schedule_onresize);
    schedule_onresize();
    """
    js = js.replace('{resize_callback_id}', resize_callback_id)
    vd.devel.loadJavascript(js=js, delay=1)

if __name__ == "__main__":
    main()

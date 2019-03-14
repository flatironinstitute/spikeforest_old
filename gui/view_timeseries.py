#!/usr/bin/env python

import argparse
import os
import vdomr as vd
from mountaintools import client as ca
import spikeforestwidgets as SFW
from spikeforest import spikeextractors as se


class TheApp():
    def __init__(self, recording_directory):
        self._recording_directory = recording_directory

    def createSession(self):
        recording = se.MdaRecordingExtractor(
            dataset_directory=self._recording_directory, download=False)
        recording = se.SubRecordingExtractor(
            parent_recording=recording, start_frame=0, end_frame=10000)
        recording = se.NumpyRecordingExtractor(
            timeseries=recording.getTraces(), samplerate=recording.getSamplingFrequency())
        W = SFW.TimeseriesWidget(recording=recording)
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
        vd.config_pyqt5()
        W = APP.createSession()
        vd.exec_javascript('console.log("test123")')
        vd.pyqt5_start(root=W, title='view_timeseries')


if __name__ == "__main__":
    main()

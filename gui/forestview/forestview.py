#!/usr/bin/env python

import argparse
import os
import vdomr as vd
from mountaintools import client as mt
from core import ForestViewMainWindow
import uuid
import json
from viewrecordingcontext import ViewRecordingContext
from views import RecordingSummaryView, TimeseriesView
import uuid
import mtlogging

recording_object = {'name': '001_synth',
 'study': 'mearec_neuronexus_noise10_K10_C32',
 'directory': 'kbucket://15734439d8cf/groundtruth/mearec_synth/neuronexus/datasets_noise10_K10_C32/001_synth',
 #'directory': '/home/magland/src/spikeforest/working/prepare_recordings/toy_recordings/example_K10',
 'description': 'One of the recordings in the mearec_neuronexus_noise10_K10_C32 study',
 'summary': {'computed_info': {'samplerate': 30000.0,
   'num_channels': 32,
   'duration_sec': 600.0},
  'plots': {},
  'true_units_info': 'sha1://b81dbb15d34f3c1b34693fe6e6a5b0b0ee3bf099/true_units_info.json'}}

class TheApp():
    def __init__(self):
        pass

    def createSession(self):
        W = ForestViewMainWindow(context=ViewRecordingContext(recording_object=recording_object))
        _register_views(W)
        _make_full_browser(W)
        return W


def main():
    parser = argparse.ArgumentParser(description='Browse SpikeForest results')
    parser.add_argument(
        '--port', help='The port to listen on (for a web service). Otherwise, attempt to launch as stand-alone GUI.', required=False, default=None)
    parser.add_argument(
        '--collection', help='The remote collection', required=False, default=None
    )
    parser.add_argument(
        '--share_id', help='The remote kbucket share_id', required=False, default=None
    )

    args = parser.parse_args()

    # Configure readonly access to kbucket
    if args.collection and args.share_id:
        mt.configRemoteReadonly(collection=args.collection,share_id=args.share_id)

    APP = TheApp()

    if args.port is not None:
        vd.config_server()
        server = vd.VDOMRServer(APP)
        server.setPort(int(args.port))
        server.start()
    else:
        vd.pyqt5_start(APP=APP, title='ForestView')

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

def _register_views(W):
    W.addViewLauncher('recording-summary', dict(
        label='Recording summary',
        view_class=RecordingSummaryView
    ))
    W.addViewLauncher('timeseries', dict(
        label='Timeseries',
        view_class=TimeseriesView
    ))


if __name__ == "__main__":
    main()

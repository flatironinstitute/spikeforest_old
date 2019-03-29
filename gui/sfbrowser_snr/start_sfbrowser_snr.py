#!/usr/bin/env python

import argparse
import os
import vdomr as vd
from mountaintools import client as mt
from sfbrowser_snr_mainwindow import SFBrowserSnrMainWindow
os.environ['SIMPLOT_SRC_DIR'] = '../../simplot'
import uuid


class TheApp():
    def __init__(self):
        pass

    def createSession(self):
        print('creating main window')
        W = SFBrowserSnrMainWindow()
        _make_full_browser(W)
        print('done creating main window')
        return W


def main():
    parser = argparse.ArgumentParser(description='Browse SpikeForest results (SNR threshold)')
    parser.add_argument(
        '--port', help='The port to listen on (for a web service). Otherwise, attempt to launch as stand-alone GUI.', required=False, default=None)

    args = parser.parse_args()

    # Configure readonly access to kbucket
    mt.configRemoteReadonly(collection='spikeforest',share_id='spikeforest.spikeforest2')

    APP = TheApp()

    if args.port is not None:
        vd.config_server()
        server = vd.VDOMRServer(APP)
        server.setPort(int(args.port))
        server.start()
    else:
        vd.pyqt5_start(APP=APP, title='SFBrowserSnr')

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

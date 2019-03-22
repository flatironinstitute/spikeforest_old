#!/usr/bin/env python

import argparse
import os
import vdomr as vd
from mountaintools import client as mt
from browse_recordings import MainWindow


class TheApp():
    def __init__(self):
        pass

    def createSession(self):
        print('creating main window')
        W = MainWindow()
        print('done creating main window')
        return W


def main():
    parser = argparse.ArgumentParser(description='Browse SpikeForest results')
    parser.add_argument(
        '--port', help='The port to listen on (for a web service). Otherwise, attempt to launch as stand-alone GUI.', required=False, default=None)
    parser.add_argument(
        '--collection', help='The remote collection', required=False, default='spikeforest'
    )
    parser.add_argument(
        '--share_id', help='The remote kbucket share_id', required=False, default='spikeforest.spikeforest2'
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
        vd.config_pyqt5()
        W = APP.createSession()
        vd.pyqt5_start(root=W, title='Browse Recordings')


if __name__ == "__main__":
    main()

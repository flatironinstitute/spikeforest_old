#!/usr/bin/env python

import os
import vdomr as vd
from cairio import client as ca
from sfbrowsermainwindow import SFBrowserMainWindow
os.environ['SIMPLOT_SRC_DIR'] = '../../simplot'


class TheApp():
    def __init__(self):
        pass

    def createSession(self):
        print('creating main window')
        W = SFBrowserMainWindow()
        print('done creating main window')
        return W


def main():
    # Configure readonly access to kbucket
    ca.autoConfig(collection='spikeforest', key='spikeforest2-readonly')

    APP = TheApp()
    server = vd.VDOMRServer(APP)
    server.start()


if __name__ == "__main__":
    main()

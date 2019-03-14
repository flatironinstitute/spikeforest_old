#!/usr/bin/env python

import os
import vdomr as vd
from mountaintools import client as ca
from sortingresultsexplorermainwindow import SortingResultsExplorerMainWindow
os.environ['SIMPLOT_SRC_DIR'] = '../../simplot'


class TheApp():
    def __init__(self):
        pass

    def createSession(self):
        print('creating main window')
        W = SortingResultsExplorerMainWindow()
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

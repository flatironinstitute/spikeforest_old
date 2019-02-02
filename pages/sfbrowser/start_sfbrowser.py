#!/usr/bin/env python

from sfbrowsermainwindow import SFBrowserMainWindow
import spikeforest as sf
import vdomr as vd
import os
os.environ['VDOMR_MODE'] = 'SERVER'
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

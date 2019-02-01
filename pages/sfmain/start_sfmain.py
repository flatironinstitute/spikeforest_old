#!/usr/bin/env python

import os
os.environ['VDOMR_MODE'] = 'SERVER'
os.environ['SIMPLOT_SRC_DIR']='../../simplot'

import vdomr as vd
import spikeforest as sf
from kbucket import client as kb
#from sfmain import sfmain
from pages.monitor_batches.monitorbatchesmainwindow import MonitorBatchesMainWindow
from pages.sfbrowser.sfbrowsermainwindow import SFBrowserMainWindow

class MainWindow(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._contents=[
            dict(label='Job Monitor',window=MonitorBatchesMainWindow()),
            dict(label='SpikeForest Browser',window=SFBrowserMainWindow())
        ]
        self._current_window=None

    def _open_item(self,item):
        self._current_window=item['window']
        self.refresh()

    def _on_home(self):
        self._current_window=None
        self.refresh()

    def render(self):
        if self._current_window:
            return vd.div(
                vd.a('home',onclick=self._on_home),
                self._current_window
            )

        elmts=[
            vd.a(item['label'],onclick=lambda item=item: self._open_item(item))
            for item in self._contents
        ]
        rows=[vd.tr(vd.td(elmt)) for elmt in elmts]
        table=vd.table(rows)
        return vd.div(
            table,
            style=dict(padding='30px')
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

import os
import vdomr as vd
import sfdata as sf
from monitorbatchesmainwindow import MonitorBatchesMainWindow
import sfdata as sf


class TheApp():
    def __init__(self):
        pass

    def createSession(self):
        W = MonitorBatchesMainWindow()
        return W


def main():
    # Configure readonly access to kbucket
    sf.kbucketConfigRemote(name='spikeforest1-readonly')
    # sf.kbucketConfigLocal()

    APP = TheApp()
    server = vd.VDOMRServer(APP)
    server.start()


if __name__ == "__main__":
    main()

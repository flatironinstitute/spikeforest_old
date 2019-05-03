import vdomr as vd
import os


class Status(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._status = ''

    def setStatus(self, status):
        self._status = status
        self.refresh()

    def render(self):
        return vd.div('STATUS: ' + self._status)


class MyApp():
    def __init__(self):
        pass

    def createSession(self):
        status = Status()
        status.setStatus('test1')

        def on_click():
            print('clicked')
            status.setStatus('clicked...')
            return 'return_string'
        root = vd.div(vd.h3('testing'), vd.h2('testing2'),
                      vd.button('push me', onclick=on_click), status)
        return root


if __name__ == "__main__":
    APP = MyApp()
    server = vd.VDOMRServer(APP)
    server.start()

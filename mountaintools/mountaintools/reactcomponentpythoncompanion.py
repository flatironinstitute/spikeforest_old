from abc import abstractmethod
import json
import sys
import select
import traceback
from copy import deepcopy
import time


class ReactComponentPythonCompanion:
    def __init__(self, iterate_timeout=1):
        self._python_state = {}
        self._javascript_state = {}
        self.original_stdout = None
        self._quit = False
        self._iterate_timeout = iterate_timeout
        pass

    # subclass must implement updateComponent
    @abstractmethod
    def updateComponent(self, prevJavascriptState):
        pass

    def iterate(self):
        pass

    # subclass may call this to update the state
    def setPythonState(self, state: dict):
        new_state = {}
        for key, val in state.items():
            if not are_equal(self._python_state.get(key, None), val):
                new_state[key] = val
        if len(new_state.keys()) > 0:
            msg = {"name": "setPythonState", "state": new_state}
            self._sendMessage(msg)
    
    def getPythonState(self, key: str, defaultval=None):
        return deepcopy(self._python_state.get(key, defaultval))
    
    def getJavaScriptState(self, key: str, defaultval=None):
        return deepcopy(self._javascript_state.get(key, defaultval))
    
    # start the message loop
    def run(self):
        self.original_stdout = sys.stdout
        sys.stdout = sys.stderr
        while True:
            self._flush_all()
            stdin_available = select.select([sys.stdin], [], [], self._iterate_timeout)[0]
            if stdin_available:
                line = sys.stdin.readline()
                try:
                    msg = json.loads(line)
                except:
                    print(line)
                    raise Exception('Error parsing message.')
                self._handleMessage(msg)
            else:
                 self.iterate()
            self._flush_all()
            if self._quit:
                break
            time.sleep(0.01)

    # internal function to handle incoming message (coming from javascript component)
    def _handleMessage(self, msg):
        if msg['name'] == 'setJavaScriptState':
            prevJavaScriptState = deepcopy(self._javascript_state)
            something_changed = False
            for key, val in msg['state'].items():
                if not are_equal(prevJavaScriptState.get(key, None), val):
                    self._javascript_state[key] = val
                    something_changed = True
            if something_changed:
                try:
                    self.updateComponent(prevJavaScriptState)
                except Exception as err:
                    traceback.print_exc()
                    self._sendMessage(dict(name="error", error="Error updating component: {}".format(repr(err))))
                self._flush_all()
        elif msg['name'] == 'quit':
            self._quit = True
            self._flush_all()
        else:
            print(msg)
            raise Exception('Unexpectected message')
    
    # internal function to send message to javascript component
    def _sendMessage(self, msg):
        print(json.dumps(msg), file=self.original_stdout)
        self._flush_all()

    def _flush_all(self):
        self.original_stdout.flush()
        sys.stdout.flush()
        sys.stderr.flush()


def are_equal(obj1, obj2):
    return (json.dumps(obj1, sort_keys=True) == json.dumps(obj2, sort_keys=True))
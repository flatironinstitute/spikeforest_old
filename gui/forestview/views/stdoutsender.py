import sys
import time

class _StdoutHandler(object):
    def __init__(self, connection):
        self._connection = connection
        self._text = ''
        self._timer = time.time()
        self._other_stdout = None

    def write(self, data):
        if self._other_stdout:
            self._other_stdout.write(data)
        self._text = self._text + str(data)
        elapsed = time.time() - self._timer
        if elapsed > 5:
            self.send()
            self._timer = time.time()

    def flush(self):
        if self._other_stdout:
            self._other_stdout.flush()

    def setOtherStdout(self, other_stdout):
        self._other_stdout = other_stdout

    def send(self):
        if self._text:
            self._connection.send(dict(name="log", text=self._text))
            self._text=''

class StdoutSender():
    def __init__(self, connection):
        self._connection = connection
        self._handler = _StdoutHandler(connection)
    def __enter__(self):
        self._old_stdout = sys.stdout
        self._old_stderr = sys.stderr
        self._handler.setOtherStdout(self._old_stdout)
        sys.stdout = self._handler
        sys.stderr = self._handler
        return dict()
    def __exit__(self, exc_type, exc_val, exc_tb):
        self._handler.send()
        sys.stdout = self._old_stdout
        sys.stderr = self._old_stderr
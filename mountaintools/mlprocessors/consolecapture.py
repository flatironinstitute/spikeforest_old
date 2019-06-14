from typing import Any
import sys
import time
import os
import tempfile


class Logger2():
    def __init__(self, file1: Any, file2: Any):
        self.file1 = file1
        self.file2 = file2

    def write(self, data: str) -> None:
        self.file1.write(data)
        self.file2.write(data)

    def flush(self) -> None:
        self.file1.flush()
        self.file2.flush()


class ConsoleCapture():
    def __init__(self):
        self._console_out = ''
        self._tmp_fname = None
        self._file_handle = None
        self._time_start = None
        self._time_stop = None
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    def start_capturing(self) -> None:
        self._tmp_fname = tempfile.mktemp(suffix='.txt')
        self._file_handle = open(self._tmp_fname, 'w')
        sys.stdout = Logger2(self._file_handle, self._original_stdout)
        sys.stderr = Logger2(self._file_handle, self._original_stderr)
        self._time_start = time.time()

    def stop_capturing(self) -> None:
        assert self._tmp_fname is not None
        self._time_stop = time.time()
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self._file_handle.close()
        with open(self._tmp_fname, 'r') as f:
            self._console_out = f.read()
        os.unlink(self._tmp_fname)

    def addToConsoleOut(self, txt: str) -> None:
        self._file_handle.write(txt)

    def runtimeInfo(self) -> dict:
        assert self._time_start is not None
        return dict(
            start_time=self._time_start - 0,
            end_time=self._time_stop - 0,
            elapsed_sec=self._time_stop - self._time_start
        )

    def consoleOut(self) -> str:
        return self._console_out

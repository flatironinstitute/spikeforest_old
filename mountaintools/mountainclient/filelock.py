import fcntl
import errno
import time
import random

class FileLock():
    def __init__(self, path, _disable_lock=False):
        self._path = path
        self._file = None
        self._disable_lock = _disable_lock
    def __enter__(self):
        if self._disable_lock:
            return
        self._file = open(self._path, 'w+')
        num_tries = 0
        while True:
            try:
                fcntl.flock(self._file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                if num_tries>10:
                    print('Locked file {} after {} tries...'.format(self._path, num_tries))
                break
            except IOError as e:
                if e.errno != errno.EAGAIN:
                    raise
                else:
                    num_tries=num_tries+1
                    time.sleep(random.uniform(0,0.1))
    def __exit__(self, type, value, traceback):
        if self._disable_lock:
            return
        fcntl.flock(self._file, fcntl.LOCK_UN)
        self._file.close()

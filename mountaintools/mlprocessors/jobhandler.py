import abc
import time
from .mountainjob import currentJobHandler, _setCurrentJobHandler


class JobHandler():
    def __init__(self):
        super().__init__()
        self._parent_job_handler = None

    @abc.abstractmethod
    def executeJob(self, job):
        pass

    @abc.abstractmethod
    def iterate(self):
        pass

    @abc.abstractmethod
    def isFinished(self):
        pass

    @abc.abstractmethod
    def halt(self):
        pass

    def wait(self, timeout=-1):
        timer = time.time()
        while not self.isFinished():
            self.iterate()
            elapsed = time.time() - timer
            if (timeout >= 0) and (elapsed > timeout):
                return False
            if not self.isFinished():
                time.sleep(0.2)
        return True

    def parentJobHandler(self):
        return self._parent_job_handler

    def __enter__(self):
        self._parent_job_handler = currentJobHandler()
        _setCurrentJobHandler(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        _setCurrentJobHandler(self._parent_job_handler)

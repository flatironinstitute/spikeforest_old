import abc
import time


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

    @abc.abstractmethod
    def cleanup(self):
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

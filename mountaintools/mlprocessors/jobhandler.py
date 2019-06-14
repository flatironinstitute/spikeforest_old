import abc
import time
from .mountainjob import MountainJob
from .mountainjobresult import MountainJobResult


class JobHandler():
    def __init__(self):
        super().__init__()
        self._parent_job_handler = None

    @abc.abstractmethod
    def executeJob(self, job: MountainJob) -> MountainJobResult:
        pass

    @abc.abstractmethod
    def iterate(self) -> None:
        pass

    @abc.abstractmethod
    def isFinished(self) -> bool:
        pass

    @abc.abstractmethod
    def halt(self) -> None:
        pass

    @abc.abstractmethod
    def cleanup(self) -> None:
        pass

    def wait(self, timeout: float=-1):
        timer = time.time()
        while not self.isFinished():
            self.iterate()
            elapsed = time.time() - timer
            if (timeout >= 0) and (elapsed > timeout):
                return False
            if not self.isFinished():
                time.sleep(0.2)
        return True

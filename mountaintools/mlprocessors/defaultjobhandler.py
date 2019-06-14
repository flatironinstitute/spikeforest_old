from .jobhandler import JobHandler
from .mountainjob import MountainJob
from .mountainjobresult import MountainJobResult


class DefaultJobHandler(JobHandler):
    def __init__(self):
        super().__init__()

    def executeJob(self, job: MountainJob) -> MountainJobResult:
        job.result._status = 'running'
        result = job._execute()
        job.result._status = 'finished'
        return result

    def iterate(self) -> None:
        pass

    def isFinished(self) -> bool:
        return True

    def halt(self) -> None:
        pass

    def cleanup(self) -> None:
        pass

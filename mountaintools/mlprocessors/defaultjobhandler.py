from .jobhandler import JobHandler


class DefaultJobHandler(JobHandler):
    def __init__(self):
        super().__init__()

    def executeJob(self, job):
        job.result._status = 'running'
        result = job._execute()
        job.result._status = 'finished'
        return result

    def iterate(self):
        pass

    def isFinished(self):
        return True

    def halt(self):
        pass

import multiprocessing
import time
import mlprocessors as mlpr
from .jobhandler import JobHandler
from .mountainjob import currentJobHandler
from .mountainjobresult import MountainJobResult


class ParallelJobHandler(JobHandler):
    def __init__(self, num_workers):
        super().__init__()
        self._num_workers = num_workers
        self._job_manager = None
        self._halted = False

    def executeJob(self, job):
        self._job_manager.addJob(job)

    def iterate(self):
        if self._halted:
            return

        self._job_manager.iterate()
    
    def isFinished(self):
        if self._halted:
            return True
        return self._job_manager.isFinished()

    def halt(self):
        self._halted = True

    def __enter__(self):
        self._job_manager = _JobManager(parent_job_handler=currentJobHandler(), num_workers=self._num_workers)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)


class _JobManager():
    def __init__(self, parent_job_handler, num_workers):
        self._parent_job_handler = parent_job_handler
        self._num_workers = num_workers
        self._processes = []

    def isFinished(self):
        for p in self._processes:
            if p['jmstatus'] != 'finished':
                return False
        return True

    def iterate(self):
        for p in self._processes:
            if p['jmstatus'] == 'running':
                if p['pipe_to_child'].poll():
                    result_obj = p['pipe_to_child'].recv()
                    p['pipe_to_child'].send('okay!')
                    p['job'].result.fromObject(result_obj)
                    p['job'].result._status = 'finished'
                    p['jmstatus'] = 'finished'
        
        num_running = 0
        for p in self._processes:
            if p['jmstatus'] == 'running':
                num_running = num_running + 1

        for p in self._processes:
            if p['jmstatus'] == 'pending':
                if num_running < self._num_workers:
                    p['jmstatus'] = 'running'
                    p['process'].start()
                    num_running = num_running + 1

    def addJob(self, job):
        pipe_to_parent, pipe_to_child = multiprocessing.Pipe()
        process = multiprocessing.Process(target=_run_job, args=(pipe_to_parent, self._parent_job_handler, job))
        self._processes.append(dict(
            job=job,
            process=process,
            pipe_to_child=pipe_to_child,
            jmstatus='pending'
        ))


def _run_job(pipe_to_parent, parent_job_handler, job):
    result0 = parent_job_handler.executeJob(job)
    result0.wait()
    pipe_to_parent.send(result0.getObject())
    # wait for message to return
    while True:
        if pipe_to_parent.poll():
            pipe_to_parent.recv()
            return
        time.sleep(0.1)

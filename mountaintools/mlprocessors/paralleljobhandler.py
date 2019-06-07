import multiprocessing
import time
import signal
import mlprocessors as mlpr
from .jobhandler import JobHandler
from .mountainjobresult import MountainJobResult


class ParallelJobHandler(JobHandler):
    def __init__(self, num_workers):
        super().__init__()
        self._num_workers = num_workers
        self._processes = []
        self._halted = False

    def executeJob(self, job):
        pipe_to_parent, pipe_to_child = multiprocessing.Pipe()
        process = multiprocessing.Process(target=_run_job, args=(pipe_to_parent, job))
        self._processes.append(dict(
            job=job,
            process=process,
            pipe_to_child=pipe_to_child,
            pjh_status='pending'
        ))

    def iterate(self):
        if self._halted:
            return

        for p in self._processes:
            if p['pjh_status'] == 'running':
                if p['pipe_to_child'].poll():
                    result_obj = p['pipe_to_child'].recv()
                    p['pipe_to_child'].send('okay!')
                    p['job'].result.fromObject(result_obj)
                    p['job'].result._status = 'finished'
                    p['pjh_status'] = 'finished'
        
        num_running = 0
        for p in self._processes:
            if p['pjh_status'] == 'running':
                num_running = num_running + 1

        for p in self._processes:
            if p['pjh_status'] == 'pending':
                if num_running < self._num_workers:
                    p['pjh_status'] = 'running'
                    p['process'].start()
                    num_running = num_running + 1
    
    def isFinished(self):
        if self._halted:
            return True
        for p in self._processes:
            if p['pjh_status'] != 'finished':
                return False
        return True

    def halt(self):
        for p in self._processes:
            if p['pjh_status'] == 'running':
                # TODO: i don't think this will actually terminate the child processes
                p['process'].terminate()
        self._halted = True

    def cleanup(self):
        pass


def _run_job(pipe_to_parent, job):
    result0 = job._execute()
    pipe_to_parent.send(result0.getObject())
    # wait for message to return
    while True:
        if pipe_to_parent.poll():
            pipe_to_parent.recv()
            return
        time.sleep(0.1)

import time
import mlprocessors as mlpr
import traceback
from .mountainjob import currentJobQueue, _setCurrentJobQueue
from .mountainjobresult import MountainJobResult


class JobQueue():
    def __init__(self, job_handler=None):
        super().__init__()

        self._all_jobs = dict()
        self._queued_jobs = dict()
        self._running_jobs = dict()
        self._finished_jobs = dict()
        self._last_job_id = 0
        self._halted = False
        self._parent_job_queue = None
        self._job_handler = job_handler
        # self._job_manager = None

    def queueJob(self, job):
        job_id = self._last_job_id + 1
        self._last_job_id = job_id
        self._queued_jobs[job_id] = job
        self._all_jobs[job_id] = job
        job_object = job.getObject()
        job_outputs = job_object['outputs']
        result_outputs = dict()
        for output_name, output0 in job_outputs.items():
            result_outputs[output_name] = dict(
                queue_job_id=job_id,
                output_name=output_name,
                output_signature=output0['signature'],
                hash=output0['signature']
            )
        obj0 = dict(
            outputs=result_outputs
        )
        result0 = MountainJobResult(result_object=obj0, job_queue=self)
        setattr(job, 'result', result0)
        return result0

    def iterate(self):
        if self._halted:
            return

        if self._job_handler:
            self._job_handler.iterate()
        self._check_for_finished_jobs()

        queued_job_ids = sorted(list(self._queued_jobs.keys()))
        job_ids_to_run = []
        for id in queued_job_ids:
            job = self._queued_jobs[id]
            if self._job_is_ready_to_run(job):
                job_ids_to_run.append(id)
        
        for id in job_ids_to_run:
            if self._halted:
                return
            job = self._queued_jobs[id]
            del self._queued_jobs[id]
            self._running_jobs[id] = job
            job.result._status = 'running'
            # self._job_manager.addJob(job)
            # first check result cache
            R0 = job._execute_check_cache()
            if R0 is not None:
                jobj = job.getObject()
                print('Using result from cache: {}'.format(jobj.get('label', jobj.get('processor_name', '<>'))))
                job.result._status = 'finished'
            else:
                self._job_handler.executeJob(job)

        if self._job_handler:
            self._job_handler.iterate()
        self._check_for_finished_jobs()
    
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

    def _check_for_finished_jobs(self):
        for jobs0 in [self._running_jobs, self._queued_jobs]:
            finished_job_ids = []
            for id, job in jobs0.items():
                if job.result.status() == 'finished':
                    finished_job_ids.append(id)
            for id in finished_job_ids:
                job = jobs0[id]
                del jobs0[id]
                self._finished_jobs[id] = job

    def _job_is_ready_to_run(self, job):
        obj0 = job.getObject(copy=False)
        inputs0 = obj0['inputs']
        all_inputs = []
        for _, input0 in inputs0.items():
            if type(input0) == list:
                all_inputs.extend(input0)
            else:
                all_inputs.append(input0)
        for input0 in all_inputs:
            if input0['path'] is None:
                qj_id = input0['object']['queue_job_id']
                output_name = input0['object']['output_name']
                qj = self._all_jobs[qj_id]
                if qj.result.status() == 'finished':
                    if qj.result.retcode == 0:
                        input0['path'] = qj.result.outputs[output_name]
                    else:
                        # in this case the input is not available because the dependent job failed
                        job.result.retcode = 7 # for now this signifies that it failed in this way
                        job.result._status = 'finished'
                        return False
                else:
                    return False
        return True
    
    def isFinished(self):
        if self._halted:
            return True
        return (self._queued_jobs == {}) and (self._running_jobs == {})

    def halt(self):
        if self._job_handler:
            self._job_handler.halt()
        self._halted = True

    def __enter__(self):
        self._parent_job_queue = currentJobQueue()
        _setCurrentJobQueue(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.halt()
        _setCurrentJobQueue(self._parent_job_queue)
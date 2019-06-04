import mlprocessors as mlpr
from .jobhandler import JobHandler
from .mountainjob import currentJobHandler
from .mountainjobresult import MountainJobResult


class QueueJobHandler(JobHandler):
    def __init__(self):
        super().__init__()

        self._all_jobs = dict()
        self._queued_jobs = dict()
        self._running_jobs = dict()
        self._finished_jobs = dict()
        self._last_job_id = 0
        self._halted = False
        # self._job_manager = None

    def executeJob(self, job):
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
        result0 = MountainJobResult(result_object=obj0, job_handler=self)
        setattr(job, 'result', result0)
        return result0

    def iterate(self):
        if self._halted:
            return

        self.parentJobHandler().iterate()
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
            self._parent_job_handler.executeJob(job)

        self.parentJobHandler().iterate()
        self._check_for_finished_jobs()

    def _check_for_finished_jobs(self):
        finished_job_ids = []
        for id, job in self._running_jobs.items():
            if job.result.status() == 'finished':
                finished_job_ids.append(id)
        for id in finished_job_ids:
            job = self._running_jobs[id]
            del self._running_jobs[id]
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
                    input0['path'] = qj.result.outputs[output_name]
                else:
                    return False
        return True
    
    def isFinished(self):
        if self._halted:
            return True
        return (self._queued_jobs == {}) and (self._running_jobs == {})

    def halt(self):
        self._halted = True

    def __enter__(self):
        # self._job_manager = _JobManager(parent_job_handler=currentJobHandler(), num_workers=self._num_workers)
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)

import time
import mlprocessors as mlpr
import traceback
import multiprocessing
from .mountainjob import MountainJob
from .mountainjobresult import MountainJobResult
from mountainclient import client as mt
from typing import Optional, List
from .jobhandler import JobHandler
from .defaultjobhandler import DefaultJobHandler


class JobQueue():
    def __init__(self, job_handler: JobHandler=DefaultJobHandler()):
        super().__init__()

        self._all_jobs: dict = dict()
        self._queued_jobs: dict = dict()
        self._running_jobs: dict = dict()
        self._finished_jobs: dict = dict()
        self._last_job_id = 0  # So that we can give a unique id to each job that has been queued
        self._halted = False  # Whether this job queue has been halted
        self._parent_job_queue = None  # Not sure if we actually support nested job queues, but for now we restore the parent job queue on exit of the with block
        self._job_handler: JobHandler = job_handler  # The job handler (e.g., parallel, slurm, default)
        # self._job_manager = None

    def queueJob(self, job: MountainJob) -> MountainJobResult:
        """Queue a job. This happens automatically by the framework when .execute() is called on a processor
        
        Parameters
        ----------
        job : MountainJob
            The job to queue
        
        Returns
        -------
        MountainJobResult
            The job result object associated with the job. Same as "job.result".
        """
        job_id = self._last_job_id + 1
        self._last_job_id = job_id
        self._queued_jobs[job_id] = job
        self._all_jobs[job_id] = job
        job_object = job.getObject()
        job_outputs = job_object['outputs']
        result_outputs = dict()
        for output_name in job_outputs.keys():
            result_outputs[output_name] = dict(
                queue_job_id=job_id,
                output_name=output_name,
                pending=True
            )
        obj0 = dict(
            outputs=result_outputs
        )
        result0 = MountainJobResult(result_object=obj0, job_queue=self)
        setattr(job, 'result', result0)
        return result0

    def iterate(self) -> None:
        """Called periodically by the framework to take care of business.
        
        Returns
        -------
        None
        """
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
        
        newly_running_jobs = []
        for id in job_ids_to_run:
            if self._halted:
                return
            job = self._queued_jobs[id]
            del self._queued_jobs[id]
            self._running_jobs[id] = job
            job.result._status = 'running'

            newly_running_jobs.append(job)

        if len(newly_running_jobs) > 0:
            print('Checking cache for {} jobs...'.format(len(newly_running_jobs)))
            newly_running_job_results_from_cache = _check_cache_for_job_results(newly_running_jobs)
            for ii, job in enumerate(newly_running_jobs):
                newly_running_job_result = newly_running_job_results_from_cache[ii]
                if newly_running_job_result is not None:
                    jobj = job.getObject()
                    print('Using result from cache: {}'.format(jobj.get('label', jobj.get('processor_name', '<>'))))
                    job.result.fromObject(newly_running_job_result.getObject())
                    job.result._status = 'finished'
                else:
                    self._job_handler.executeJob(job)

        if self._job_handler:
            self._job_handler.iterate()
        self._check_for_finished_jobs()
    
    def wait(self, timeout: float=-1) -> bool:
        """Wait until all queued jobs have completed or until timeout.
        
        Parameters
        ----------
        timeout : float, optional
            The maximum number of seconds to wait. The default (-1) means it will never time out.
        
        Returns
        -------
        bool
            Whether all the jobs have finished. Will return False if the timeout has been reached.
        """
        timer = time.time()
        while not self.isFinished():
            self.iterate()
            elapsed = time.time() - timer
            if (timeout >= 0) and (elapsed > timeout):
                return False
            if not self.isFinished():
                time.sleep(0.2)
        return True

    def _check_for_finished_jobs(self) -> None:
        for jobs0 in [self._running_jobs, self._queued_jobs]:
            finished_job_ids = []
            for id, job in jobs0.items():
                if job.result.status() == 'finished':
                    finished_job_ids.append(id)
            for id in finished_job_ids:
                job = jobs0[id]
                del jobs0[id]
                self._finished_jobs[id] = job

    def _job_is_ready_to_run(self, job: MountainJob) -> bool:
        obj0 = job.getObject(copy=False)
        inputs0 = obj0['inputs']
        all_inputs: List[dict] = []
        for _, input0 in inputs0.items():
            if type(input0) == list:
                all_inputs.extend(input0)
            else:
                all_inputs.append(input0)
        for input0 in all_inputs:
            if input0.get('pending', False):
                qj_id = input0['object']['queue_job_id']
                output_name = input0['object']['output_name']
                qj = self._all_jobs[qj_id]
                if qj.result.status() == 'finished':
                    if qj.result.retcode == 0:
                        input0['path'] = qj.result.outputs[output_name]
                        input0['hash'] = mt.computeFileSha1(input0['path'])
                    else:
                        # in this case the input is not available because the dependent job failed
                        job.result.retcode = 7  # for now this signifies that it failed in this way
                        job.result._status = 'finished'
                        return False
                else:
                    return False
        return True
    
    def isFinished(self) -> bool:
        """Whether all queued jobs have finished.
        
        Returns
        -------
        bool
            True if all queued jobs have finished.
        """
        if self._halted:
            return True
        return (self._queued_jobs == {}) and (self._running_jobs == {})

    def halt(self) -> None:
        """Stop the job queue in its tracks, and send the halt message to the job handler.
        
        Returns
        -------
        None
        """
        if self._job_handler:
            self._job_handler.halt()
        self._halted = True

    def __enter__(self):
        self._parent_job_queue = currentJobQueue()
        _setCurrentJobQueue(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.halt()
        if self._job_handler:
            self._job_handler.cleanup()
        _setCurrentJobQueue(self._parent_job_queue)


class _Internal():
    def __init__(self):
        self.current_job_queue: Optional[JobQueue] = None

_internal = _Internal()


def currentJobQueue() -> Optional[JobQueue]:
    return _internal.current_job_queue


def _setCurrentJobQueue(jqueue: Optional[JobQueue]) -> None:
    _internal.current_job_queue = jqueue


def _check_cache_for_job_results(jobs: List[MountainJob]) -> List[Optional[MountainJobResult]]:
    pool = multiprocessing.Pool(10)
    result_objects = pool.map(_execute_job_check_cache, [job.getObject() for job in jobs])
    pool.close()
    pool.join()
    results: List[Optional[MountainJobResult]] = []
    for robj in result_objects:
        if robj:
            results.append(MountainJobResult(result_object=robj))
        else:
            results.append(None)
    return results


def _execute_job_check_cache(job_object: dict) -> Optional[dict]:
    job = MountainJob(job_object=job_object)
    result = job._execute_check_cache()
    if result:
        return result.getObject()
    else:
        return None

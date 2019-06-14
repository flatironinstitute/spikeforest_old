import multiprocessing
import os
import time
import random
import signal
import shutil
import mlprocessors as mlpr
from .jobhandler import JobHandler
from .mountainjobresult import MountainJobResult
from .shellscript import ShellScript
from mountainclient import FileLock
from mountainclient import client as mt
from typing import Optional, List
import json

DEFAULT_JOB_TIMEOUT = 1200


class SlurmJobHandler(JobHandler):
    def __init__(self, working_dir: str):
        """Constructor for slurm job handler

        Parameters
        ----------
        working_dir : str
            The working directory which must not yet exist, but its parent must exist. Will be removed at the end.
        """
        super().__init__()
        if os.path.exists(working_dir):
            raise Exception('Working directory already exists: {}'.format(working_dir))
        os.mkdir(working_dir)
        self._batch_types: dict = dict()
        self._batches: dict = dict()
        self._halted: bool = False
        self._last_batch_id: int = 0
        self._working_dir: str = working_dir
        self._unassigned_jobs: List[mlpr.MountainJob] = []

    def addBatchType(self, *,
                     name: str,
                     num_workers_per_batch: int,
                     num_cores_per_job: int,
                     use_slurm: bool,
                     time_limit_per_batch: Optional[float]=None,  # number of seconds or None
                     max_simultaneous_batches: Optional[int]=None,
                     additional_srun_opts: List[str]=[]
                     ) -> None:
        """Add a batch type to the slurm job handler.

        Parameters
        ----------
        name : str
            Name of the batch type (e.g., cpu, gpu)
        num_workers_per_batch : int
            Number of worker tasks to spawn for each batch
        num_cores_per_job : int
            Number of cpu cores to allocate for each worker task
        use_slurm : bool
            Whether to use slurm (if False, will use local computer without slurm)
        time_limit_per_batch : Optional[float], optional
            If a number, the maximum duration of a batch in seconds, by default None
        additional_srun_opts : List[str], optional
            A list of additional string options to send to srun (only applies of use_slurm is True), by default []

        Returns
        -------
        None
        """
        if name in self._batch_types:
            raise Exception('Batch type already exists: {}'.format(name))
        self._batch_types[name] = dict(
            num_workers_per_batch=num_workers_per_batch,
            num_cores_per_job=num_cores_per_job,
            use_slurm=use_slurm,
            time_limit_per_batch=time_limit_per_batch,
            max_simultaneous_batches=max_simultaneous_batches,
            additional_srun_opts=additional_srun_opts
        )

    def executeJob(self, job: mlpr.MountainJob) -> MountainJobResult:
        """Queue a job to run in a batch. This is called from the framework (e.g., the job queue)

        Parameters
        ----------
        job : mlpr.MountainJob
            The job to run. The job can specify the batch type in its compute requirements.
            The default batch type is "default".

        Returns
        -------
        MountainJobResult
            The job result object. Same as "job.result".
        """
        job_timeout = job.getObject().get('timeout', None)
        if job_timeout is None:
            job_timeout = DEFAULT_JOB_TIMEOUT
        compute_requirements = job.getObject().get('compute_requirements', {})
        batch_type_name = compute_requirements.get('batch_type', 'default')
        if batch_type_name not in self._batch_types:
            raise Exception('No batch type: {}'.format(batch_type_name))
        batch_type = self._batch_types[batch_type_name]
        if batch_type['time_limit_per_batch'] is not None:
            if job_timeout > batch_type['time_limit_per_batch']:
                raise Exception('Cannot execute job. Job timeout exceeds time limit: {} > {}'.format(job_timeout, batch_type['time_limit_per_batch']))
        self._unassigned_jobs.append(job)
        return job.result

    def iterate(self) -> None:
        """Called by the framework to take care of business.

        Returns
        -------
        None
        """
        # Iterate the batches that are not finished
        for _, b in self._batches.items():
            if not b.isFinished():
                b.iterate()

        # Return if we have been halted
        if self._halted:
            return

        # Handle the unassigned jobs
        unassigned_jobs_after = []
        for job in self._unassigned_jobs:
            if not self._handle_unassigned_job(job):
                # Unable to assign the job, so we'll try next iteration
                unassigned_jobs_after.append(job)
        self._unassigned_jobs = unassigned_jobs_after

    def isFinished(self) -> bool:
        """Whether all queued jobs have finished

        Returns
        -------
        bool
            True if all queued jobs have finished
        """
        if self._halted:
            return True
        if len(self._unassigned_jobs) > 0:
            # Some job is unassigned
            return False
        for b in self._batches.values():
            if b.isRunning():
                if b.hasJob():
                    # Some batch has a running job
                    return False
        return True

    def halt(self) -> None:
        """Stop the job handler in its tracks.

        Returns
        -------
        None
        """
        # Halt all of the batches that are not finished
        for _, b in self._batches.items():
            if not b.isFinished():
                b.halt()
        self._halted = True

    def cleanup(self) -> None:
        """Remove the working directory

        Returns
        -------
        None
        """
        try:
            shutil.rmtree(self._working_dir)
        except:
            time.sleep(3)
            shutil.rmtree(self._working_dir)

    def _handle_unassigned_job(self, job: mlpr.MountainJob):
        compute_requirements = job.getObject().get('compute_requirements', {})
        batch_type_name = compute_requirements.get('batch_type', 'default')
        if batch_type_name not in self._batch_types:
            raise Exception('No such batch type in slurm job handler: {}'.format(batch_type_name))
        batch_type = self._batch_types[batch_type_name]

        # See if we can add a job to an existing batch that has a vacancy
        for _, b in self._batches.items():
            if b.batchTypeName() == batch_type_name:
                if b.isRunning():
                    if b.canAddJob(job):
                        b.addJob(job)
                        return True

        # See if there is anything waiting to start and count up the number of running batches
        num_running_batches_of_type = 0
        for _, b in self._batches.items():
            if b.batchTypeName() == batch_type_name:
                if b.isWaitingToStart() or b.isPending():
                    # we'll wait for the batch to start before assigning it
                    return False
                if not b.isFinished():
                    num_running_batches_of_type = num_running_batches_of_type + 1

        # Check if we would exceed max num of simultaneous batches
        if batch_type['max_simultaneous_batches'] is not None:
            if num_running_batches_of_type >= batch_type['max_simultaneous_batches']:
                # we can't create a new batch now
                return False

        # we need to create a new batch and we'll add the job later
        batch_id = self._last_batch_id + 1
        self._last_batch_id = batch_id
        # we put a random string in the working directory so we don't have a chance of interference from previous runs
        print('Creating new batch', batch_id)
        new_batch = _Batch(
            working_dir=self._working_dir + '/batch_{}_{}'.format(batch_id, _random_string(8)),
            batch_label='batch {} ({})'.format(batch_id, batch_type_name),
            batch_type_name=batch_type_name,
            batch_type=batch_type
        )
        self._batches[batch_id] = new_batch
        new_batch.start()
        # we'll add the job later
        return False


class _Batch():
    def __init__(self, working_dir: str, batch_label: str, batch_type_name: str, batch_type: dict):
        """Constructor for _Batch class internal to SlurmJobHandler

        Parameters
        ----------
        working_dir : str
            The working directory within the slurm job handler working directory
        batch_label : str
            A label for display purposes
        batch_type_name : str
            The name of the batch type for this batch
        batch_type : dict
            The batch type dict (see SlurmJobHandler.addBatchType)
        """
        os.mkdir(working_dir)
        self._status = 'pending'
        self._time_started: Optional[float] = None
        self._working_dir = working_dir
        self._batch_label = batch_label
        self._batch_type = batch_type
        self._batch_type_name = batch_type_name
        self._num_workers = batch_type['num_workers_per_batch']
        self._num_cores_per_job = batch_type['num_cores_per_job']
        self._use_slurm = batch_type['use_slurm']
        self._time_limit = batch_type['time_limit_per_batch']
        self._additional_srun_opts = batch_type['additional_srun_opts']
        self._workers: List[_Worker] = []
        self._had_a_job = False

        # Create the workers
        for i in range(self._num_workers):
            self._workers.append(_Worker(base_path=self._working_dir + '/worker_{}'.format(i)))

        self._slurm_process = _SlurmProcess(
            working_dir=self._working_dir,
            num_workers=self._num_workers,
            num_cores_per_job=self._num_cores_per_job,
            additional_srun_opts=self._additional_srun_opts,
            use_slurm=self._use_slurm,
            time_limit=self._time_limit
        )

    def batchTypeName(self) -> str:
        return self._batch_type_name

    def batchType(self) -> dict:
        return self._batch_type

    def isPending(self) -> bool:
        return self._status == 'pending'

    def isWaitingToStart(self) -> bool:
        return self._status == 'waiting'

    def isRunning(self) -> bool:
        return self._status == 'running'

    def isFinished(self) -> bool:
        return self._status == 'finished'

    def timeStarted(self) -> Optional[float]:
        return self._time_started

    def elapsedSinceStarted(self) -> float:
        if not self._time_started:
            return 0
        return time.time() - self._time_started

    def iterate(self) -> None:
        """Periodically take care of business

        Returns
        -------
        None
            [description]
        """
        if self.isPending():
            pass
        elif self.isWaitingToStart():
            # first iterate all the workers so they can do what they need to do
            for w in self._workers:
                w.iterate()
            for w in self._workers:
                if w.hasStarted():
                    # Some worker has started, so I guess this batch has started.
                    self._status = 'running'
                    self._time_started = time.time()
                    break
            if self._status != 'running':
                # We are still not running. Hmmmm. Let's check something...

                # the following is probably not needed
                # but I suspected some trouble with our ceph
                # file system where the expected file
                # was not being detected until I added this
                # line. hmmmmm.
                x = os.listdir(self._working_dir)
                if len(x) == 0:
                    assert('Unexpected problem. We should at least have a running.txt and a *.py file here.')
        elif self.isRunning():
            # first iterate all the workers so they can do what they need to do
            for w in self._workers:
                w.iterate()

            # If we had a job in the past and we
            # haven't had anything to do for last 30 seconds, then
            # let's just end.
            if self._had_a_job:
                still_doing_stuff = False
                for w in self._workers:
                    if w.hasJob():
                        still_doing_stuff = True
                    else:
                        if w.everHadJob():
                            elapsed = w.elapsedTimeSinceLastJob()
                            assert elapsed is not None, "Unexpected elapsed is None"
                            if elapsed <= 30:
                                still_doing_stuff = True
                if not still_doing_stuff:
                    self.halt()
        elif self.isFinished():
            # We are finished so there's nothing to do
            pass

    def canAddJob(self, job: mlpr.MountainJob) -> bool:
        """Return True if we are able to add job, based on timing info, etc.

        Parameters
        ----------
        job : mlpr.MountainJob
            Job to potentially add

        Returns
        -------
        bool
            Whether the job can be added
        """
        if self.isFinished():
            # We are finished, so we can't add any jobs
            return False
        # Determine the specified timeout of the job
        job_timeout = job.getObject().get('timeout', None)
        if job_timeout is None:
            # if job doesn't have timeout, we use the default
            job_timeout = DEFAULT_JOB_TIMEOUT
        # See if adding this job would exceed the time limit
        if self._time_limit is not None:
            if job_timeout + self.elapsedSinceStarted() > self._time_limit + 5:
                # We would exceed the time limit. Can't add the job
                return False
        # If some worker has a vacancy then we can add the job
        for w in self._workers:
            if not w.hasJob():
                return True
        # Otherwise, we have no vacancy for a new job
        return False

    def hasJob(self) -> bool:
        """Return True if some worker has a job
        """
        for w in self._workers:
            if w.hasJob():
                return True
        return False

    def addJob(self, job: mlpr.MountainJob) -> None:
        """Add a job to the batch. Presumably it was already checked with canAddJob()

        Parameters
        ----------
        job : mlpr.MountainJob
            The job to add

        Returns
        -------
        None
        """
        if self._status != 'running':
            raise Exception('Cannot add job to batch that is not running.')

        # Determine number running, for display information
        num_running = 0
        for w in self._workers:
            if w.hasJob():
                num_running = num_running + 1

        # The job object
        jobj = job.getObject()
        print('Adding job to batch {} ({}/{}): {}'.format(self._batch_label, num_running + 1, self._num_workers, jobj.get('label', jobj.get('processor_name', '<>'))))

        # Since we are adding a job, we declare that we have had a job
        self._had_a_job = True

        # Add the job to a vacant worker
        for w in self._workers:
            if not w.hasJob():
                w.setJob(job)
                return

        # This would be unexpected because we should have already checked with canAddJob()
        raise Exception('Unexpected: Unable to add job to batch. Unexpected -- no vacancies.')

    def start(self) -> None:
        """Start the patch

        Returns
        -------
        None
        """
        assert self._status == 'pending', "Unexpected... cannot start a batch that is not pending."

        # Write the running.txt file
        running_fname = self._working_dir + '/running.txt'
        with FileLock(running_fname + '.lock', exclusive=True):
            with open(running_fname, 'w') as f:
                f.write('batch.')

        # Start the slurm process
        self._slurm_process.start()

        self._status = 'waiting'
        # self._time_started = time.time()  # instead of doing it here, let's wait until a worker has actually started.

    def halt(self) -> None:
        """Halt the batch
        """
        # Remove the running.txt file which should trigger the workers to end
        running_fname = self._working_dir + '/running.txt'
        if os.path.exists(running_fname):
            with FileLock(running_fname + '.lock', exclusive=True):
                os.remove(self._working_dir + '/running.txt')
        self._status = 'finished'
        # wait a bit for it to resolve on its own (because we removed the running.txt)
        if not self._slurm_process.wait(5):
            print('Waiting for slurm process to end.')
            self._slurm_process.wait(5)
        # now force the halt
        self._slurm_process.halt()


class _Worker():
    def __init__(self, base_path: str):
        """Constructor for _Worker of _Batch of SlurmJobHandler

        Parameters
        ----------
        base_path : str
            The base path of file names that this worker deals with
            [base_path]_claimed.txt
            [base_path]_job.json
            [base_path]_result.json
            and corresponding lock files
        """
        self._job: Optional[mlpr.MountainJob] = None
        self._job_finish_timestamp: Optional[float] = None
        self._base_path: str = base_path

    def hasJob(self) -> bool:
        """Whether this worker has a job
        """
        if self._job is not None:
            return True
        return False

    def everHadJob(self) -> bool:
        """Whether this worker ever had a job
        """
        if self._job is not None:
            return True
        if self._job_finish_timestamp is not None:
            return True
        return False

    def elapsedTimeSinceLastJob(self) -> Optional[float]:
        """If the worker ever had a job, returns elapsed number of seconds since that job completed. Otherwise returns None.
        """
        if self._job is not None:
            return 0
        if self._job_finish_timestamp is not None:
            elapsed = time.time() - self._job_finish_timestamp
            return elapsed
        return None

    def setJob(self, job: mlpr.MountainJob) -> None:
        """Set the job for this worker. Essentially writes the job object to a file which is picked up by the running worker process.

        Parameters
        ----------
        job : mlpr.MountainJob
            The job to run.

        Returns
        -------
        None
        """
        self._job = job
        job_object = self._job.getObject()
        job_fname = self._base_path + '_job.json'
        with FileLock(job_fname + '.lock', exclusive=True):
            with open(job_fname, 'w') as f:
                json.dump(job_object, f)

    def hasStarted(self) -> bool:
        """Returns whether the worker (not the job) has started
        """
        return os.path.exists(self._base_path + '_claimed.txt')

    def iterate(self) -> None:
        """Take care of business of the worker
        """
        if not self._job:
            # If we don't have a job, then we don't need to take care of any business.
            return
        job_fname = self._base_path + '_job.json'
        result_fname = self._base_path + '_result.json'
        result_obj: Optional[dict] = None
        with FileLock(result_fname + '.lock', exclusive=False):
            if os.path.exists(result_fname):
                # The result file exists. So the active job must have completed.
                with open(result_fname, 'r') as f:
                    # Here's the result object that we will deal with below
                    result_obj = json.load(f)

                # Let's remove the _job.json.complete file if it exists
                if os.path.exists(job_fname + '.complete'):
                    os.remove(job_fname + '.complete')
                # Let's move the _job.json file to the _job.json.complete file
                os.rename(job_fname, job_fname + '.complete')

                # Similarly for the _result.json.complete file
                if os.path.exists(result_fname + '.complete'):
                    os.remove(result_fname + '.complete')
                os.rename(result_fname, result_fname + '.complete')

            elif os.path.exists(result_fname + '.error'):
                # It looks like there was an error processing the job
                # This is not a job error, this is a mountaintools error
                # So we are going to read the exception information from the .error
                # file, print it, and then raise an exception
                # This is serious and should not happen.
                with open(result_fname + '.error', 'r') as f:
                    print(f.read())
                raise Exception('Unexpected error processing job in batch.')

        if result_obj:
            # Here's the result that we read above
            self._job.result.fromObject(result_obj)
            self._job.result._status = 'finished'
            # We no longer have a job, and we should set the finished timestamp
            self._job = None
            self._job_finish_timestamp = time.time()


class _SlurmProcess():
    def __init__(self, working_dir: str, num_workers: int, additional_srun_opts: List[str], use_slurm: bool, time_limit: Optional[float], num_cores_per_job: int):
        """Constructor for a slurm process (corresponding to a batch)

        Parameters
        ----------
        working_dir : str
            The working directory for this slurm process, where we will put some temporary scripts and stuff
        num_workers : int
            Number of workers in the batch
        additional_srun_opts : List[str]
            Additional opts to pass to srun
        use_slurm : bool
            Whether we are actually using slurm
        time_limit : Optional[float]
            The time limit in seconds for this slurm batch
        num_cores_per_job : int
            Number of cpu cores devoted to each job / worker
        """
        self._working_dir = working_dir
        self._num_workers = num_workers
        self._additional_srun_opts = additional_srun_opts
        self._use_slurm = use_slurm
        self._num_cores_per_job = num_cores_per_job
        if self._num_cores_per_job is None:
            self._num_cores_per_job = 1
        self._time_limit = time_limit

    def start(self) -> None:
        """Start the slurm process
        """

        # This script is run by each worker (slurm task) in the batch
        srun_py_script = ShellScript("""
                #!/usr/bin/env python

                import os
                import time
                import json
                import random
                import traceback
                from mountainclient import FileLock
                import mlprocessors as mlpr

                working_dir = '{working_dir}'
                num_workers = {num_workers}
                running_fname = '{running_fname}'

                # Let's claim a place and determine which worker number we are
                worker_num = None
                # wait a random amount of time before starting
                time.sleep(random.uniform(0, 0.1))
                for i in range(num_workers):
                    fname = working_dir + '/worker_{}_claimed.txt'.format(i)
                    if not os.path.exists(fname):
                        with FileLock(fname + '.lock', exclusive=True):
                            if not os.path.exists(fname):
                                with open(fname, 'w') as f:
                                    f.write('claimed')
                                worker_num = i
                                break
                if worker_num is None:
                    raise Exception('Unable to claim worker file.')

                job_fname = working_dir + '/worker_{}_job.json'.format(worker_num)
                result_fname = working_dir + '/worker_{}_result.json'.format(worker_num)

                try:  # We are going to catch any exceptions and report them back to the parent process
                    num_found = 0
                    while True:
                        # Check whether running file exists
                        with FileLock(running_fname + '.lock', exclusive=False):
                            if not os.path.exists(running_fname):
                                print('Running file not found. Stopping worker.')
                                break

                        # Check to see if we have a job to do
                        job_object = None
                        with FileLock(job_fname + '.lock', exclusive=False):
                            if (os.path.exists(job_fname)) and not (os.path.exists(result_fname)):
                                num_found = num_found + 1
                                with open(job_fname, 'r') as f:
                                    job_object = json.load(f)
                        
                        # If we have a job to do, then let's do it
                        if job_object:
                            job = mlpr.MountainJob(job_object = job_object)
                            result = job._execute(print_console_out=False)
                            with FileLock(result_fname + '.lock', exclusive=True):
                                with open(result_fname, 'w') as f:
                                    # Write the result
                                    json.dump(result.getObject(), f)
                        time.sleep(0.2)
                except:
                    # report the exception back to the parent process by writing a _result.json.error file
                    with FileLock(result_fname + '.lock', exclusive=True):
                        with open(result_fname + ".error", 'w') as f:
                            f.write(traceback.format_exc())
            """, script_path=os.path.join(self._working_dir, 'execute_batch_srun.py')
                                     )
        srun_py_script.substitute('{working_dir}', self._working_dir)
        srun_py_script.substitute('{num_workers}', self._num_workers)
        srun_py_script.substitute('{running_fname}', self._working_dir + '/running.txt')
        srun_py_script.write()

        srun_opts = []
        srun_opts.extend(self._additional_srun_opts)
        srun_opts.append('-n {}'.format(self._num_workers))
        srun_opts.append('-c {}'.format(self._num_cores_per_job))
        if self._time_limit is not None:
            srun_opts.append('--time {}'.format(round(self._time_limit / 60) + 1))
        if self._use_slurm:
            srun_sh_script = ShellScript("""
               #!/bin/bash
               set -e

               _term() {
                   echo "Terminating srun process..."
                   kill -INT "$srun_pid" 2>/dev/null
                   # srun needs two signals
                   sleep 0.3
                   kill -INT "$srun_pid" 2>/dev/null
                }

                trap _term SIGINT SIGTERM

                export NUM_WORKERS={num_cores_per_job}
                export MKL_NUM_THREADS=$NUM_WORKERS
                export NUMEXPR_NUM_THREADS=$NUM_WORKERS
                export OMP_NUM_THREADS=$NUM_WORKERS

                export DISPLAY=""

                srun {srun_opts} {srun_py_script} &
                srun_pid=$!
                wait $srun_pid
            """, keep_temp_files=False)
            srun_sh_script.substitute('{srun_opts}', ' '.join(srun_opts))
            srun_sh_script.substitute('{srun_py_script}', srun_py_script.scriptPath())
            srun_sh_script.substitute('{num_cores_per_job}', self._num_cores_per_job)

            srun_sh_script.start()
            self._srun_sh_scripts = [srun_sh_script]
        else:
            self._srun_sh_scripts = []
            for _ in range(self._num_workers):
                srun_sh_script = ShellScript("""
                    #!/bin/bash
                    set -e

                    export NUM_WORKERS={num_cores_per_job}
                    export MKL_NUM_THREADS=$NUM_WORKERS
                    export NUMEXPR_NUM_THREADS=$NUM_WORKERS
                    export OMP_NUM_THREADS=$NUM_WORKERS

                    export DISPLAY=""

                    {srun_py_script}
                """, keep_temp_files=False)
                srun_sh_script.substitute('{srun_py_script}', srun_py_script.scriptPath())
                srun_sh_script.substitute('{num_cores_per_job}', self._num_cores_per_job)

                srun_sh_script.start()
                self._srun_sh_scripts.append(srun_sh_script)

    def wait(self, timeout) -> bool:
        """Wait until the process or processes have finished

        Parameters
        ----------
        timeout : [type]
            Amount of time to wait

        Returns
        -------
        bool
            True if the processes have finished. False if timeout occurred.
        """
        timer = time.time()
        while True:
            all_finished = True
            for x in self._srun_sh_scripts:
                if not x.isFinished():
                    all_finished = False
            if all_finished:
                break
            elapsed = time.time() - timer
            if elapsed >= timeout:
                return False
            time.sleep(0.2)
        return True

    def halt(self) -> None:
        """Halt the processes
        """
        for x in self._srun_sh_scripts:
            if not x.isFinished():
                if not x.stopWithSignal(sig=signal.SIGTERM, timeout=5):
                    print('Warning: unable to stop slurm script.')


def _random_string(num: int):
    """Generate random string of a given length.
    """
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))

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
import json

DEFAULT_JOB_TIMEOUT = 1200


class SlurmJobHandler(JobHandler):
    def __init__(self, working_dir):
        super().__init__()
        if os.path.exists(working_dir):
            raise Exception('Working directory already exists: {}'.format(working_dir))
        os.mkdir(working_dir)
        self._batch_types = dict()
        self._batches = dict()
        self._halted = False
        self._last_batch_id = 0
        self._working_dir = working_dir
        self._unassigned_jobs = []

    def addBatchType(self, *,
                     name,
                     num_workers_per_batch,
                     num_cores_per_job,
                     use_slurm,
                     time_limit_per_batch=None,  # number of seconds or None
                     additional_srun_opts=[]
                     ):
        if name in self._batch_types:
            raise Exception('Batch type already exists: {}'.format(name))
        self._batch_types[name] = dict(
            num_workers_per_batch=num_workers_per_batch,
            num_cores_per_job=num_cores_per_job,
            use_slurm=use_slurm,
            time_limit_per_batch=time_limit_per_batch,
            additional_srun_opts=additional_srun_opts
        )

    def executeJob(self, job):
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

    def iterate(self):
        if self._halted:
            return
        for _, b in self._batches.items():
            if not b.isFinished():
                b.iterate()
        new_unassigned_jobs = []
        for job in self._unassigned_jobs:
            if not self._handle_unassigned_job(job):
                new_unassigned_jobs.append(job)
        self._unassigned_jobs = new_unassigned_jobs

    def isFinished(self):
        if self._halted:
            return True
        if len(self._unassigned_jobs) > 0:
            return False
        for b in self._batches.values():
            if b.isRunning():
                if b.hasJob():  # todo: implement
                    return False
        return True

    def halt(self):
        for _, b in self._batches.items():
            if not b.isFinished():
                b.halt()
        self._halted = True

    def cleanup(self):
        try:
            shutil.rmtree(self._working_dir)
        except:
            time.sleep(3)
            shutil.rmtree(self._working_dir)

    def _handle_unassigned_job(self, job):
        compute_requirements = job.getObject().get('compute_requirements', {})
        batch_type_name = compute_requirements.get('batch_type', 'default')
        if batch_type_name not in self._batch_types:
            raise Exception('No such batch type in slurm job handler: {}'.format(batch_type_name))
        batch_type = self._batch_types[batch_type_name]

        for _, b in self._batches.items():
            if b.batchTypeName() == batch_type_name:
                if b.isRunning():
                    if b.canAddJob(job):
                        b.addJob(job)
                        return True
        for _, b in self._batches.items():
            if b.batchTypeName() == batch_type_name:
                if b.isWaitingToStart() or b.isPending():
                    # we'll wait for the batch to start before assigning it
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
    def __init__(self, working_dir, batch_label, batch_type_name, batch_type):
        os.mkdir(working_dir)
        self._status = 'pending'
        self._time_started = None
        self._working_dir = working_dir
        self._batch_label = batch_label
        self._batch_type = batch_type
        self._batch_type_name = batch_type_name
        self._num_workers = batch_type['num_workers_per_batch']
        self._num_cores_per_job = batch_type['num_cores_per_job']
        self._use_slurm = batch_type['use_slurm']
        self._time_limit = batch_type['time_limit_per_batch']
        self._additional_srun_opts = batch_type['additional_srun_opts']
        self._workers = []
        self._had_a_job = False

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

    def batchTypeName(self):
        return self._batch_type_name

    def batchType(self):
        return self._batch_type

    def isPending(self):
        return self._status == 'pending'

    def isWaitingToStart(self):
        return self._status == 'waiting'

    def isRunning(self):
        return self._status == 'running'

    def isFinished(self):
        return self._status == 'finished'

    def timeStarted(self):
        return self._time_started

    def elapsedSinceStarted(self):
        if not self._time_started:
            return 0
        return time.time() - self._time_started

    def iterate(self):
        if self.isPending():
            pass
        elif self.isWaitingToStart():
            for w in self._workers:
                w.iterate()
            for w in self._workers:
                if w.hasStarted():
                    self._status = 'running'
                    self._time_started = time.time()
                    break
                if self._status != 'running':
                    # the following is probably not needed
                    # but I suspected some trouble with our ceph
                    # file system where the expected file
                    # was not being detected until I added this
                    # line. hm.
                    x = os.listdir(self._working_dir)
                    if len(x) == 0:
                        assert('Unexpected problem. We should at least have a running.txt and a *.py file here.')
        elif self.isRunning():
            for w in self._workers:
                w.iterate()
            if self._had_a_job:
                still_doing_stuff = False
                for w in self._workers:
                    if w.hadJob(5):
                        still_doing_stuff = True
                if not still_doing_stuff:
                    self.halt()
        elif self.isFinished():
            pass

    def canAddJob(self, job):
        if self.isFinished():
            return False
        job_timeout = job.getObject().get('timeout', None)
        if job_timeout is None:
            job_timeout = DEFAULT_JOB_TIMEOUT
        if self._time_limit is not None:
            if job_timeout + self.elapsedSinceStarted() > self._time_limit + 5:
                return False
        for w in self._workers:
            if not w.hasJob():
                return True
    
    def hasJob(self):
        has_some_job = False
        for w in self._workers:
            if w.hasJob(delay=10):
                has_some_job = True
        return has_some_job

    def addJob(self, job):
        if self._status != 'running':
            raise Exception('Cannot add job to batch that is not running.')
        num_running = 0
        for w in self._workers:
            if w.hasJob():
                num_running = num_running + 1
        jobj = job.getObject()
        print('Adding job to batch {} ({}/{}): {}'.format(self._batch_label, num_running + 1, self._num_workers, jobj.get('label', jobj.get('processor_name', '<>'))))
        self._had_a_job = True
        for w in self._workers:
            if not w.hasJob():
                w.setJob(job)
                return
        raise Exception('Unexpected: Unable to add job to batch')

    def start(self):
        assert self._status == 'pending'
        self._slurm_process.start()
        running_fname = self._working_dir + '/running.txt'
        with FileLock(running_fname + '.lock', exclusive=True):
            with open(running_fname, 'w') as f:
                f.write('batch.')
        self._status = 'waiting'
        self._time_started = time.time()

    def halt(self):
        print('Halting batch...')
        running_fname = self._working_dir + '/running.txt'
        with FileLock(running_fname + '.lock', exclusive=True):
            os.remove(self._working_dir + '/running.txt')
        self._status = 'finished'
        self._slurm_process.halt()


class _Worker():
    def __init__(self, base_path):
        self._job = None
        self._job_finish_timestamp = None
        self._base_path = base_path

    def hasJob(self, delay=None):
        if self._job is not None:
            return True
        return False

    def hadJob(self, delay):
        if self._job is not None:
            return True
        if self._job_finish_timestamp is not None:
            elapsed = time.time() - self._job_finish_timestamp
            if elapsed <= delay:
                return True
        return False

    def setJob(self, job):
        self._job = job
        job_object = self._job.getObject()
        job_fname = self._base_path + '_job.json'
        with FileLock(job_fname + '.lock', exclusive=True):
            with open(job_fname, 'w') as f:
                json.dump(job_object, f)
    
    def hasStarted(self):
        return os.path.exists(self._base_path + '_claimed.txt')

    def iterate(self):
        if not self._job:
            return
        job_fname = self._base_path + '_job.json'
        result_fname = self._base_path + '_result.json'
        result_obj = None
        with FileLock(result_fname + '.lock', exclusive=False):
            if os.path.exists(result_fname):
                with open(result_fname, 'r') as f:
                    result_obj = json.load(f)
                if os.path.exists(job_fname + '.complete'):
                    os.remove(job_fname + '.complete')
                os.rename(job_fname, job_fname + '.complete')
                if os.path.exists(result_fname + '.complete'):
                    os.remove(result_fname + '.complete')
                os.rename(result_fname, result_fname + '.complete')
            elif os.path.exists(result_fname + '.error'):
                with open(result_fname + '.error', 'r') as f:
                    print(f.read())
                raise Exception('Unexpected error processing job in batch.')

        if result_obj:
            self._job.result.fromObject(result_obj)
            self._job.result._status = 'finished'
            self._job = None
            self._job_finish_timestamp = time.time()


class _SlurmProcess():
    def __init__(self, working_dir, num_workers, additional_srun_opts, use_slurm, time_limit, num_cores_per_job):
        self._working_dir = working_dir
        self._num_workers = num_workers
        self._additional_srun_opts = additional_srun_opts
        self._use_slurm = use_slurm
        self._num_cores_per_job = num_cores_per_job
        if self._num_cores_per_job is None:
            self._num_cores_per_job = 1
        self._time_limit = time_limit

    def start(self):
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

                num_found = 0
                while True:
                    with FileLock(running_fname + '.lock', exclusive=False):
                        if not os.path.exists(running_fname):
                            break
                    job_object = None
                    with FileLock(job_fname + '.lock', exclusive=False):
                        if (os.path.exists(job_fname)) and not (os.path.exists(result_fname)):
                            num_found = num_found + 1
                            with open(job_fname, 'r') as f:
                                job_object = json.load(f)
                    if job_object:
                        job = mlpr.MountainJob(job_object = job_object)
                        try:
                            result = job.execute()
                            with FileLock(result_fname + '.lock', exclusive=True):
                                with open(result_fname, 'w') as f:
                                    json.dump(result.getObject(), f)
                        except:
                            with FileLock(result_fname + '.lock', exclusive=True):
                                with open(result_fname + ".error", 'w') as f:
                                    f.write(traceback.format_exc())
                    time.sleep(0.2)
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

    def halt(self):
        for x in self._srun_sh_scripts:
            if not x.stopWithSignal(sig=signal.SIGTERM, timeout=2):
                print('Warning: unable to stop slurm script.')


def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))

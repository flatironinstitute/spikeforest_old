import multiprocessing
import os
import time
import random
import mlprocessors as mlpr
from .jobhandler import JobHandler
from .mountainjob import currentJobHandler
from .mountainjobresult import MountainJobResult
from .shellscript import ShellScript
from mountainclient import FileLock
from mountainclient import client as mt
import json


class SlurmJobHandler(JobHandler):
    def __init__(
        self,
        working_dir,
        workers_per_batch=12,
        max_simultaneous_batches=4,
        use_slurm=True,
        srun_opts=[]
    ):
        super().__init__()
        if os.path.exists(working_dir):
            raise Exception('Working directory already exists: {}'.format(working_dir))
        os.mkdir(working_dir)
        self._opts = dict(
            workers_per_batch=workers_per_batch,
            max_simultaneous_batches=max_simultaneous_batches,
            srun_opts=srun_opts,
            use_slurm=use_slurm
        )
        self._running_batches = dict()
        self._halted = False
        self._last_batch_id = 0
        self._working_dir = working_dir

    def executeJob(self, job):
        batch_ids = sorted(list(self._running_batches.keys()))
        for id in batch_ids:
            b = self._running_batches[id]
            if b.canAddJob(job):
                b.addJob(job)
                return
        batch_id = self._last_batch_id + 1
        self._last_batch_id = batch_id
        # important to put a random string in the working directory so we don't have a chance of interference from previous runs
        nb = _Batch(num_workers=self._opts['workers_per_batch'], working_dir=self._working_dir + '/batch_{}_{}'.format(batch_id, _random_string(8)), srun_opts=self._opts['srun_opts'], use_slurm=self._opts['use_slurm'])
        if not nb.canAddJob(job):
            raise Exception('Cannot add job to new batch.')
        self._running_batches[batch_id] = nb
        nb.addJob(job)

    def iterate(self):
        if self._halted:
            return
        batch_ids_to_remove = []
        for id, b in self._running_batches.items():
            if b.isFinished():
                batch_ids_to_remove.append(id)
            else:
                b.iterate()
        for id in batch_ids_to_remove:
            del self._running_batches[id]

        num_running = 0
        num_pending = 0
        for _, b in self._running_batches.items():
            if b.isRunning():
                num_running = num_running + 1
            elif b.isPending():
                num_pending = num_pending + 1

        if (num_pending > 0) and (num_running < self._opts['max_simultaneous_batches']):
            for _, b in self._running_batches.items():
                if b.isPending() and (num_running < self._opts['max_simultaneous_batches']):
                    b.start()
                    num_running = num_running + 1

    def isFinished(self):
        if self._halted:
            return True
        return (self._running_batches == {})

    def halt(self):
        for _, b in self._running_batches.items():
            b.halt()
        self._halted = True

    def __enter__(self):
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        for b in self._running_batches.values():
            b.halt()
        super().__exit__(exc_type, exc_val, exc_tb)


class _Batch():
    def __init__(self, num_workers, working_dir, srun_opts, use_slurm):
        os.mkdir(working_dir)
        self._status = 'pending'
        self._working_dir = working_dir
        self._num_workers = num_workers
        self._srun_opts = srun_opts
        self._use_slurm = use_slurm
        self._workers = []
        for i in range(self._num_workers):
            self._workers.append(_Worker(base_path=self._working_dir + '/worker_{}'.format(i)))
        self._slurm_process = _SlurmProcess(working_dir=self._working_dir, num_workers=self._num_workers, srun_opts=self._srun_opts, use_slurm=self._use_slurm)

    def isPending(self):
        return self._status == 'pending'

    def isRunning(self):
        return self._status == 'running'

    def isFinished(self):
        return self._status == 'finished'

    def iterate(self):
        if self.isPending():
            pass
        elif self.isRunning():
            for w in self._workers:
                w.iterate()
            has_some_job = False
            for w in self._workers:
                if w.hasJob(delay=10):
                    has_some_job = True
            if not has_some_job:
                os.remove(self._working_dir + '/running.txt')
                self._status = 'finished'
        elif self.isFinished():
            pass

    def canAddJob(self, job):
        if self.isFinished():
            return False
        for w in self._workers:
            if not w.hasJob():
                return True

    def addJob(self, job):
        for w in self._workers:
            if not w.hasJob():
                w.setJob(job)
                return
        raise Exception('Unexpected: Unable to add job to batch')

    def start(self):
        assert self._status == 'pending'
        self._slurm_process.start()
        with open(self._working_dir + '/running.txt', 'w') as f:
            f.write('batch is running.')
        self._status = 'running'

    def halt(self):
        os.remove(self._working_dir + '/running.txt')
        self._slurm_process.halt()


class _Worker():
    def __init__(self, base_path):
        self._job = None
        self._job_finish_timestamp = None
        self._base_path = base_path

    def hasJob(self, delay=None):
        if self._job is not None:
            return True
        if delay is not None:
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

    def iterate(self):
        if not self._job:
            return
        job_fname = self._base_path + '_job.json'
        result_fname = self._base_path + '_result.json'
        result_obj = None
        with FileLock(result_fname + '.lock', exclusive=False):
            if os.path.exists(result_fname):
                with open(result_fname, 'r') as f:
                    result_obj = obj = json.load(f)
        if result_obj:
            self._job.result.fromObject(obj)
            self._job.result._status = 'finished'
            self._job = None
            os.remove(job_fname)
            os.remove(result_fname)
            self._job_finish_timestamp = time.time()


class _SlurmProcess():
    def __init__(self, working_dir, num_workers, srun_opts, use_slurm):
        self._working_dir = working_dir
        self._num_workers = num_workers
        self._num_cpus_per_worker = 2
        self._srun_opts = srun_opts
        self._use_slurm = use_slurm

    def start(self):
        srun_py_script = ShellScript("""
                #!/usr/bin/env python

                import os
                import time
                import json
                import random
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
                        result = job.execute()
                        with FileLock(result_fname + '.lock', exclusive=True):
                            with open(result_fname, 'w') as f:
                                json.dump(result.getObject(), f)
                    time.sleep(0.2)
            """, script_path=os.path.join(self._working_dir, 'execute_batch_srun.py')
                                     )
        srun_py_script.substitute('{working_dir}', self._working_dir)
        srun_py_script.substitute('{num_workers}', self._num_workers)
        srun_py_script.substitute('{running_fname}', self._working_dir + '/running.txt')
        srun_py_script.write()

        srun_opts = []
        srun_opts.extend(self._srun_opts)
        srun_opts.append('-n {}'.format(self._num_workers))
        srun_opts.append('-c {}'.format(self._num_cpus_per_worker))
        if self._use_slurm:
            srun_sh_script = ShellScript("""
                #!/bin/bash
                set -e

                srun {srun_opts} {srun_py_script}
            """, keep_temp_files=False)
            srun_sh_script.substitute('{srun_opts}', ' '.join(srun_opts))
        else:
            srun_sh_script = ShellScript("""
                #!/bin/bash
                set -e

                for i in {1..{num_workers}}; do
                    {srun_py_script} &
                done

                while :
                do
                    sleep 1
                done
            """, keep_temp_files=False)
            srun_sh_script.substitute('{num_workers}', self._num_workers)

        srun_sh_script.substitute('{srun_py_script}', srun_py_script.scriptPath())

        self._srun_sh_script = srun_sh_script
        self._srun_sh_script.start()

    def halt(self):
        self._srun_sh_script.stop()


def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))

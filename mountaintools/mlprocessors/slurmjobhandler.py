import multiprocessing
import time
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
    ):
        super().__init__()
        self._opts = dict(
            workers_per_batch=workers_per_batch,
            max_simultaneous_batches=max_simultaneous_batches
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
        nb = _Batch(num_workers=self._opts['workers_per_batch'], working_dir=working_dir + '/batch_{}'.format(batch_id))
        if not nb.canAddJob(job):
            raise Exception('Cannot add job to new batch.')
        self._running_batches[batch_id] = nb
        nb.addJob(job)

    def iterate(self):
        if self._halted:
            return
        for id, b in self._running_batches.items():
            if b.isFinished():
                del self._running_batches[id]
            else:
                b.iterate()

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
        for id, b in self._running_batches.items():
            b.halt()
        self._halted = True

    def __enter__(self):
        return super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        super().__exit__(exc_type, exc_val, exc_tb)


class _Batch():
    def __init__(self, num_workers, working_dir):
        self._opts = opts
        self._status = 'pending'
        self._working_dir = working_dir
        self._num_workers = num_workers
        self._workers = []
        for i in range(self._num_workers):
            self._workers.append(_Worker(base_path=self._working_dir + '/worker_{}'.format(i)))
        self._slurm_process = _SlurmProcess(working_dir=self._working_dir, num_workers=self._num_workers)
    
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
                if w.hasJob():
                    has_some_job = True
            if not has_some_job:
                self._status = 'finished'
        elif self.isFinished():
            pass

    def canAddJob(self, job):
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


class _Worker():
    def __init__(self, base_path):
        self._job = None
        self._base_path = base_path
    
    def hasJob(self):
        return self._job is not None
    
    def setJob(self, job):
        self._job = job
        job_object = self._job.getObject()
        job_fname = self._base_path + '/_job.json'
        with FileLock(job_fname + '.lock', exclusive=True):
            with open(job_fname, 'w') as f:
                json.dump(job_object, f)
    
    def iterate(self):
        if not self._job:
            return
        result_fname = self._base_path + '/_result.json'
        with FileLock(result_fname + '.lock', exclusive=False):
            with open(result_fname, 'r') as f:
                obj = json.load(f)
        self._job.result.fromObject(obj)
        self._job.result.status = 'finished'
        self._job = None


class _SlurmProcess():
    def __init__(self, working_dir, num_workers):
        self._working_dir = working_dir
        self._num_workers = num_workers
        self._num_cpus_per_worker = 2
    
    def start(self):
        srun_py_script = ShellScript("""
            #!/usr/bin/env python

            import os
            from mountainclient import FileLock

            working_dir = '{working_dir}'
            num_workers = {num_workers}

            worker_num = None
            for i in range(num_workers):
                fname = working_dir + '/worker_{}_claimed.txt'
                with FileLock(fname + '.lock'.format(i), exclusive=True):
                    if not os.path.exists(fname):
                        with open(fname, w) as f:
                            f.write('claimed')
                        worker_num = i
                        break
            if worker_num is None:
                raise Exception('Unable to claim worker file.')

            finish!


            local_client = MountainClient()

            job_objects = local_client.loadObject(path = '{jobs_path}')
            jobs = [MountainJob(job_object=obj) for obj in job_objects]

            executeBatch(jobs=jobs, label='{label}', num_workers=None, compute_resource=None, halt_key={halt_key}, job_status_key={job_status_key}, job_result_key={job_result_key}, srun_opts=None, job_index_file='{job_index_file}', cached_results_only={cached_results_only})
        """, script_path=os.path.join(temp_path, 'execute_batch_srun.py'), keep_temp_files=keep_temp_files)
        srun_py_script.substitute('{working_dir}', self._working_dir)
        srun_py_script.substitute('{num_workers}', self._num_workers)
        srun_py_script.substitute('{jobs_path}', jobs_path)
        srun_py_script.substitute('{label}', label)
        if halt_key:
            srun_py_script.substitute('{halt_key}', json.dumps(halt_key))
        else:
            srun_py_script.substitute('{halt_key}', 'None')
        if job_status_key:
            srun_py_script.substitute('{job_status_key}', json.dumps(job_status_key))
        else:
            srun_py_script.substitute('{job_status_key}', 'None')
        if job_result_key:
            srun_py_script.substitute('{job_result_key}', json.dumps(job_result_key))
        else:
            srun_py_script.substitute('{job_result_key}', 'None')
        srun_py_script.substitute('{cached_results_only}', str(cached_results_only))
        srun_py_script.substitute('{job_index_file}', job_index_file)
        srun_py_script.write()

        srun_opts = []
        srun_opts.append('-n {}'.format(self._num_workers))
        srun_opts.append('-c {}'.format(self._num_cpus_per_worker))
        srun_sh_script = ShellScript("""
            #!/bin/bash
            set -e

            srun {srun_opts} {srun_py_script}
        """, keep_temp_files=False)
        srun_sh_script.substitute('{srun_opts}', ' '.join(srun_opts))
        srun_sh_script.substitute('{srun_py_script}', srun_py_script.scriptPath())

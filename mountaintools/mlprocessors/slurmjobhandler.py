import multiprocessing
import os
import time
import random
import signal
import mlprocessors as mlpr
from .jobhandler import JobHandler
from .mountainjobresult import MountainJobResult
from .shellscript import ShellScript
from mountainclient import FileLock
from mountainclient import client as mt
import json

DEFAULT_JOB_TIMEOUT = 1200


class SlurmJobHandler(JobHandler):
    def __init__(
        self,
        working_dir,
        workers_per_batch=12,
        gpu_workers_per_batch=2,
        time_limit_per_batch=None,  # number of seconds or none
        use_slurm=True,
        srun_opts=[]
    ):
        super().__init__()
        if os.path.exists(working_dir):
            raise Exception('Working directory already exists: {}'.format(working_dir))
        os.mkdir(working_dir)
        self._opts = dict(
            workers_per_batch=workers_per_batch,
            gpu_workers_per_batch=gpu_workers_per_batch,
            srun_opts=srun_opts,
            use_slurm=use_slurm,
            time_limit_per_batch=time_limit_per_batch
        )
        self._running_batches = dict()
        self._halted = False
        self._last_batch_id = 0
        self._working_dir = working_dir

    def executeJob(self, job):
        job_timeout = job.getObject().get('timeout', None)
        if job_timeout is None:
            job_timeout = DEFAULT_JOB_TIMEOUT
        if self._opts['time_limit_per_batch'] is not None:
            if job_timeout + 30 > self._opts['time_limit_per_batch']:
                raise Exception('Cannot execute job. Job timeout exceeds time limit: {} + 30 > {}'.format(job_timeout, self._opts['time_limit_per_batch']))
        batch_ids = sorted(list(self._running_batches.keys()))
        for id in batch_ids:
            b = self._running_batches[id]
            if b.canAddJob(job):
                b.addJob(job)
                return
        compute_requirements = job.getObject().get('compute_requirements', {})
        gpu_job = compute_requirements.get('gpu', False)
        if gpu_job:
            num_workers = self._opts['gpu_workers_per_batch']
        else:
            num_workers = self._opts['workers_per_batch']
        batch_id = self._last_batch_id + 1
        self._last_batch_id = batch_id
        # important to put a random string in the working directory so we don't have a chance of interference from previous runs
        nb = _Batch(
            num_workers=num_workers,
            working_dir=self._working_dir + '/batch_{}_{}'.format(batch_id, _random_string(8)),
            srun_opts=self._opts['srun_opts'],
            use_slurm=self._opts['use_slurm'],
            time_limit=self._opts['time_limit_per_batch'],
            example_job=job,
            batch_label='{}'.format(batch_id)
        )
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

        for _, b in self._running_batches.items():
            if b.isPending():
                b.start()

    def isFinished(self):
        if self._halted:
            return True
        return (self._running_batches == {})

    def halt(self):
        for _, b in self._running_batches.items():
            b.halt()
        self._halted = True


class _Batch():
    def __init__(self, num_workers, working_dir, srun_opts, use_slurm, time_limit, example_job, batch_label):
        os.mkdir(working_dir)
        self._status = 'pending'
        self._working_dir = working_dir
        self._num_workers = num_workers
        self._srun_opts = srun_opts
        self._use_slurm = use_slurm
        self._time_started = None
        self._time_limit = time_limit
        self._workers = []
        self._is_gpu = False
        self._batch_label = batch_label
        if example_job:
            compute_requirements = example_job.getObject().get('compute_requirements', {})
        else:
            compute_requirements = {}
        if self._use_slurm:
            self._is_gpu = compute_requirements.get('gpu', False)
        self._num_cores_per_job = compute_requirements.get('num_cores', None)
            
        for i in range(self._num_workers):
            self._workers.append(_Worker(base_path=self._working_dir + '/worker_{}'.format(i)))
        self._slurm_process = _SlurmProcess(
            working_dir=self._working_dir, num_workers=self._num_workers, srun_opts=self._srun_opts, use_slurm=self._use_slurm,
            time_limit=time_limit, gpu=self._is_gpu, num_cores_per_job=self._num_cores_per_job
        )

    def isPending(self):
        return self._status == 'pending'

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
        compute_requirements = job.getObject().get('compute_requirements', {})
        if self._use_slurm:
            if (compute_requirements.get('gpu', False) != self._is_gpu):
                return False
            if (compute_requirements.get('num_cores', False) != self._num_cores_per_job):
                return False
        job_timeout = job.getObject().get('timeout', None)
        if job_timeout is None:
            job_timeout = DEFAULT_JOB_TIMEOUT
        if self._time_limit is not None:
            if job_timeout + self.elapsedSinceStarted() + 30 > self._time_limit:
                return False
        for w in self._workers:
            if not w.hasJob():
                return True

    def addJob(self, job):
        num_running = 0
        for w in self._workers:
            if w.hasJob():
                num_running = num_running + 1
        jobj = job.getObject()
        print('Adding job to batch {} ({}/{}): {}'.format(self._batch_label, num_running + 1, self._num_workers, jobj.get('label', jobj.get('processor_name', '<>'))))
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
        self._time_started = time.time()

    def halt(self):
        print('Halting batch...')
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
                    result_obj = json.load(f)
        if result_obj:
            self._job.result.fromObject(result_obj)
            self._job.result._status = 'finished'
            self._job = None
            if os.path.exists(job_fname + '.complete'):
                os.remove(job_fname + '.complete')
            os.rename(job_fname, job_fname + '.complete')
            if os.path.exists(result_fname + '.complete'):
                os.remove(result_fname + '.complete')
            os.rename(result_fname, result_fname + '.complete')
            self._job_finish_timestamp = time.time()


class _SlurmProcess():
    def __init__(self, working_dir, num_workers, srun_opts, use_slurm, time_limit, gpu, num_cores_per_job):
        self._working_dir = working_dir
        self._num_workers = num_workers
        self._srun_opts = srun_opts
        self._use_slurm = use_slurm
        self._num_cores_per_job = num_cores_per_job
        if self._num_cores_per_job is None:
            self._num_cores_per_job = 1
        self._time_limit = time_limit
        self._is_gpu = gpu

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
        srun_opts.append('-c {}'.format(self._num_cores_per_job))
        if self._is_gpu:
            # TODO: this needs to be configured somewhere
            srun_opts.extend(['-p gpu', '--gres=gpu:1', '--constraint=v100'])
        if self._time_limit is not None:
            srun_opts.append('--time {}'.format(round(self._time_limit / 60)))
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

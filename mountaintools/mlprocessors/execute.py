import multiprocessing
import time
from .mountainjob import MountainJob

def _create_job_from_kwargs(aa):
    return createJob(aa['proc'], **aa['kwargs'])

def createJobs(proc, argslist, *, pool_size=15):
    pool = multiprocessing.Pool(pool_size)
    jobs=pool.map(_create_job_from_kwargs, [dict(proc=proc, kwargs=kwargs) for kwargs in argslist])
    pool.close()
    pool.join()
    return jobs

def createJob(
    proc,
    _container=None,
    _use_cache=True,
    _force_run=None,
    _keep_temp_files=None,
    _label=None,
    _timeout=None,
    **kwargs
):
    timer=time.time()
    job = MountainJob()
    job.initFromProcessor(
        proc, 
        _label=_label,
        _force_run=_force_run,
        _keep_temp_files=_keep_temp_files,
        _container=_container,
        _use_cache=_use_cache,
        _timeout=_timeout,
        **kwargs
    )
    return job

def execute(
    proc,
    _container=None,
    _use_cache=True,
    _force_run=None,
    _keep_temp_files=None,
    _label=None,
    **kwargs
):
    job = createJob(proc, _container=_container, _use_cache=_use_cache, _force_run=_force_run, _keep_temp_files=_keep_temp_files, _label=_label, **kwargs)
    result = job.execute()
    return result

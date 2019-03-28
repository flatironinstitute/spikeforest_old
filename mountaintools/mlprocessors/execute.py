from .createjobs import createJob
import mtlogging

def execute(
    proc,
    _container=None,
    _use_cache=True,
    _force_run=None,
    _keep_temp_files=None,
    _label=None,
    **kwargs
):
    job = createJob(proc, _container=_container, _use_cache=_use_cache, _force_run=_force_run, _keep_temp_files=_keep_temp_files, _label=_label, _verbose=False, **kwargs)
    result = job.execute()
    return result

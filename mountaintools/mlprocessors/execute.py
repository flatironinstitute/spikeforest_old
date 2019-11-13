from .createjobs import createJob
from typing import Optional


def execute(
    proc,
    _container: Optional[str]=None,
    _use_cache: bool=True,
    _skip_failing: Optional[bool]=None,
    _skip_timed_out: Optional[bool]=None,
    _force_run: Optional[bool]=None,
    _keep_temp_files: Optional[bool]=None,
    _label: Optional[str]=None,
    **kwargs
):
    job = createJob(proc, _container=_container, _use_cache=_use_cache, _skip_failing=_skip_failing, _skip_timed_out=_skip_timed_out, _force_run=_force_run, _keep_temp_files=_keep_temp_files, _label=_label, _verbose=False, **kwargs)
    result = job.execute()
    return result

# from spikesorters import MountainSort4
import mlprocessors as mlpr

import multiprocessing
import random
class LocalComputeResource():
    def __init__(self,num_parallel,srun_opts=None):
        self._num_parallel=num_parallel
        self._exit_event = multiprocessing.Event()
        self._srun_opts = srun_opts

    def __enter__(self):
        from mountaintools import client as mt
        resource_name='local_resource_'+_random_string(6)
        self._process=multiprocessing.Process(target=_run_local_compute_resource, args=(resource_name,self._num_parallel, self._exit_event, self._srun_opts))
        self._process.start()
        
        return dict(resource_name=resource_name,collection=None,kachery_name=None)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._exit_event.set()
        print('Stopping local compute resource')
        self._process.join(5)
        print('.')
        self._process.terminate()
        
def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))

def _run_local_compute_resource(resource_name, num_parallel, exit_event, srun_opts=None):
    import mlprocessors as mlpr
    from mountaintools import client as mt
    server=mlpr.ComputeResourceServer(
        resource_name=resource_name,
        collection=None,
        kachery_name=None
    )
    server.setNumParallel(num_parallel)
    if srun_opts is not None:
        server.setSrunOptsString(srun_opts)
    server.start(exit_event=exit_event)

# with LocalComputeResource(num_parallel=4) as compute_resource:
#     jobs = MountainSort4.createJobs([
#         dict(
#             recording_dir='test',
#             firings_out='firings.mda',
#             detect_sign=-1,
#             adjacency_radius=50
#         )
#     ])
#     mlpr.executeBatch(jobs=jobs, compute_resource=compute_resource)
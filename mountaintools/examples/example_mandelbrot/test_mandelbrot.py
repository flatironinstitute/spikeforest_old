import pytest
import random
import multiprocessing
import os

def init_temp_dirs(temporary_path):
    sha1_cache_dir = temporary_path / 'sha1-cache'
    sha1_cache_dir.mkdir()
    cairio_dir = temporary_path / 'cairio'
    cairio_dir.mkdir()
    os.environ['KBUCKET_CACHE_DIR']=str(sha1_cache_dir)
    os.environ['CAIRIO_DIR']=str(cairio_dir)

def test_mandelbrot(tmp_path):
    init_temp_dirs(tmp_path)

    from mountaintools import client as mt
    import mlprocessors as mlpr
    from .mandelbrot import compute_mandelbrot, show_mandelbrot, combine_subsampled_mandelbrot, ComputeMandelbrot, compute_mandelbrot_parallel
    import numpy as np

    result=ComputeMandelbrot.execute(
        num_iter=10,
        num_x=50,
        output_npy=dict(ext='.npy', upload=True)
    )
    X=np.load(mt.realizeFile(result.outputs['output_npy']))

    Y=compute_mandelbrot_parallel(
        num_iter=10,
        num_x=50,
        num_parallel=3,
        compute_resource=None,
        _force_run=True
    )

    Z=compute_mandelbrot_parallel(
        num_iter=10,
        num_x=50,
        num_parallel=3,
        compute_resource=None,
        _force_run=False
    )

    print(X.shape, Y.shape, Z.shape)

    assert np.all(np.isclose(X,Y))
    assert np.all(np.isclose(X,Z))

class LocalComputeResource():
    def __init__(self,num_parallel):
        self._num_parallel=num_parallel
    def __enter__(self):
        resource_name='local_resource_'+_random_string(6)
        self._process=multiprocessing.Process(target=_run_local_compute_resource, args=(resource_name,self._num_parallel))
        self._process.start()
        return dict(resource_name=resource_name,collection=None,share_id=None)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._process.terminate()

def _run_local_compute_resource(resource_name, num_parallel):
    import mlprocessors as mlpr
    server=mlpr.ComputeResourceServer(
        resource_name=resource_name,
        collection=None,
        share_id=None
    )
    server.setNumParallel(num_parallel)
    server.start()

def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))

def test_mandelbrot_compute_resource(tmp_path):
    init_temp_dirs(tmp_path)
    with LocalComputeResource(num_parallel=4) as compute_resource:
        from mountaintools import client as mt
        import mlprocessors as mlpr
        from .mandelbrot import compute_mandelbrot, show_mandelbrot, combine_subsampled_mandelbrot, ComputeMandelbrot, compute_mandelbrot_parallel
        import numpy as np

        result=ComputeMandelbrot.execute(
            num_iter=10,
            num_x=50,
            output_npy=dict(ext='.npy', upload=True)
        )
        X=np.load(mt.realizeFile(result.outputs['output_npy']))

        Y=compute_mandelbrot_parallel(
            num_iter=10,
            num_x=50,
            num_parallel=3,
            compute_resource=compute_resource,
            _force_run=True
        )

        assert np.all(np.isclose(X,Y))
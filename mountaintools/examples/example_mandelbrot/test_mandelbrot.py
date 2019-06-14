import random
import multiprocessing
import os
import tempfile
import shutil
import pytest


@pytest.mark.test_mandelbrot
def test_mandelbrot():
    from mountaintools import client as mt
    import mlprocessors as mlpr
    from .mandelbrot import compute_mandelbrot, show_mandelbrot, combine_subsampled_mandelbrot, ComputeMandelbrot, compute_mandelbrot_parallel
    import numpy as np

    num_x = 4000

    result = ComputeMandelbrot.execute(
        num_iter=10,
        num_x=num_x,
        output_npy=dict(ext='.npy', upload=True)
    )
    X = np.load(mt.realizeFile(result.outputs['output_npy']))

    Y = compute_mandelbrot_parallel(
        num_iter=10,
        num_x=num_x,
        num_parallel=3,
        use_slurm=False,
        _force_run=True
    )

    Z = compute_mandelbrot_parallel(
        num_iter=10,
        num_x=num_x,
        num_parallel=3,
        use_slurm=False,
        _force_run=False
    )

    print(X.shape, Y.shape, Z.shape)

    assert np.all(np.isclose(X, Y))
    assert np.all(np.isclose(X, Z))


@pytest.mark.test_mandelbrot_slurm
def test_mandelbrot_slurm():
    from mountaintools import client as mt
    import mlprocessors as mlpr
    from .mandelbrot import compute_mandelbrot, show_mandelbrot, combine_subsampled_mandelbrot, ComputeMandelbrot, compute_mandelbrot_parallel
    import numpy as np

    num_x = 4000

    result = ComputeMandelbrot.execute(
        num_iter=10,
        num_x=num_x,
        output_npy=dict(ext='.npy', upload=True)
    )
    X = np.load(mt.realizeFile(result.outputs['output_npy']))

    Y = compute_mandelbrot_parallel(
        num_iter=10,
        num_x=num_x,
        num_parallel=3,
        use_slurm=True,
        _force_run=True
    )

    Z = compute_mandelbrot_parallel(
        num_iter=10,
        num_x=num_x,
        num_parallel=3,
        use_slurm=True,
        _force_run=False
    )

    print(X.shape, Y.shape, Z.shape)

    assert np.all(np.isclose(X, Y))
    assert np.all(np.isclose(X, Z))


@pytest.mark.test3
@pytest.mark.errors
def test_mandelbrot_errors():
    from mountaintools import client as mt
    import mlprocessors as mlpr
    from .mandelbrot import ComputeMandelbrotWithError, combine_subsampled_mandelbrot
    import numpy as np

    num_iter = 10
    num_x = 50
    num_parallel = 1
    subsampling_factor = num_parallel

    job_args = [
        dict(
            num_x=num_x,
            num_iter=num_iter,
            subsampling_factor=subsampling_factor,
            subsampling_offset=offset,
            output_npy=dict(ext='.npy', upload=True),
            throw_error=(offset == 0),
            _force_run=False
            # _container='sha1://87319c2856f312ccc3187927ae899d1d67b066f9/03-20-2019/mountaintools_basic.simg'
        )
        for offset in range(subsampling_factor)
    ]

    jobs = ComputeMandelbrotWithError.createJobs(job_args)

    results = []
    for job in jobs:
        results.append(job.execute())

    X_list = []
    for result0 in results:
        if result0.retcode == 0:
            X0 = np.load(mt.realizeFile(result0.outputs['output_npy']))
            X_list.append(X0)
        else:
            print('Warning: retcode is non-zero for job.')
            print('============================================= BEGIN CONSOLE OUT ==========================================')
            print(mt.realizeFile(result0.console_out))
            print('============================================= END CONSOLE OUT ==========================================')

    if len(X_list) > 0:
        _ = combine_subsampled_mandelbrot(X_list)


class TemporaryDirectory():
    def __init__(self):
        pass

    def __enter__(self):
        self._path = tempfile.mkdtemp()
        return self._path

    def __exit__(self, exc_type, exc_val, exc_tb):
        shutil.rmtree(self._path)

    def path(self):
        return self._path


def _random_string(num):
    return ''.join(random.choices('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ', k=num))

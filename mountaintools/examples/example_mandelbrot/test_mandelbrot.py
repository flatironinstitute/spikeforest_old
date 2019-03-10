
def test_mandelbrot():
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

import numpy as np
from matplotlib import pyplot as plt
import mlprocessors as mlpr
from mountaintools import client as mt
import multiprocessing

# Helper function for mandelbrot iterations
def compute_mandelbrot_helper(c, num_iter):
    output = np.zeros(c.shape)
    z = np.zeros(c.shape, np.complex64)
    for it in range(num_iter):
        notdone = np.less(z.real*z.real + z.imag*z.imag, 4.0)
        output[notdone] = it
        z[notdone] = z[notdone]**2 + c[notdone]
    output[output == num_iter-1] = 0
    return output

# Compute the mandelbrot set
def compute_mandelbrot(*, xmin=-2, xmax=0.5, ymin=-1.25, ymax=1.25, num_x=1000, num_iter=1000, subsampling_factor=1, subsampling_offset=0):
    num_y=int(num_x/(xmax-xmin)*(ymax-ymin))
    r1 = xmin+np.arange(num_x)/num_x*(xmax-xmin)
    r1 = r1[subsampling_offset::subsampling_factor]
    r2 = ymin+np.arange(num_y)/num_y*(ymax-ymin)
    #r1 = np.linspace(xmin, xmax, num_x, dtype=np.float32)
    #r2 = np.linspace(ymin, ymax, num_y, dtype=np.float32)
    c = r1 + r2[:,None]*1j
    n3 = compute_mandelbrot_helper(c,num_iter)
    n3 = n3.astype('float32')
    return n3.T

def combine_subsampled_mandelbrot(X_list):
    subsampling_factor=len(X_list)
    num_x=np.sum([X0.shape[0] for X0 in X_list])
    num_y=X_list[0].shape[1]
    X=np.zeros((num_x,num_y))
    for offset, X0 in enumerate(X_list):
        X[offset::subsampling_factor,:]=X0
    return X

# Display the mandelbrot set
def show_mandelbrot(X):
    fig = plt.figure(frameon=False)
    dpi=96
    fig.set_size_inches(X.shape[1]/dpi,X.shape[0]/dpi)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.imshow(np.log(X.T+0.1), cmap='hot')
    #fig.savefig('test1.png', dpi=dpi)
    #plt.close()

# Wrap it in a MountainTools processor
class ComputeMandelbrot(mlpr.Processor):
    NAME = 'ComputeMandelbrot'
    VERSION = '0.1.3'

    xmin = mlpr.IntegerParameter('The minimum x value', optional=True, default=-2)
    xmax = mlpr.IntegerParameter('The maximum x value', optional=True, default=0.5)
    ymin = mlpr.IntegerParameter('The minimum y value', optional=True, default=-1.25)
    ymax = mlpr.IntegerParameter('The maximum y value', optional=True, default=1.25)
    num_x = mlpr.IntegerParameter('The number of points (resolution) in the x dimension', optional=True, default=1000)
    num_iter = mlpr.IntegerParameter('Number of iterations', optional=True, default=1000)
    subsampling_factor = mlpr.IntegerParameter('Subsampling factor (1 means no subsampling)', optional=True, default=1)
    subsampling_offset = mlpr.IntegerParameter('Subsampling offset', optional=True, default=0)

    output_npy = mlpr.Output('The output .npy file.')

    def __init__(self):
        mlpr.Processor.__init__(self)

    def run(self):
        if self.subsampling_factor>1:
            print('Using subsampling factor {}, offset {}'.format(self.subsampling_factor, self.subsampling_offset))
        X = compute_mandelbrot(
            xmin=self.xmin, xmax=self.xmax, 
            ymin=self.ymin, ymax=self.ymax, 
            num_x=self.num_x, 
            num_iter=self.num_iter, 
            subsampling_factor=self.subsampling_factor,
            subsampling_offset=self.subsampling_offset
        )
        np.save(self.output_npy,X)

def compute_mandelbrot_parallel(*, xmin=-2, xmax=0.5, ymin=-1.25, ymax=1.25, num_x=1000, num_iter=1000, num_parallel=1, compute_resource=None, _force_run=False):
    subsampling_factor=num_parallel
    jobs=[]

    job_args=[
        dict(
            num_x=num_x,
            num_iter=num_iter,
            subsampling_factor=subsampling_factor,
            subsampling_offset=offset,
            output_npy=dict(ext='.npy', upload=True),
            _force_run=_force_run
        )
        for offset in range(subsampling_factor)
    ]

    jobs = ComputeMandelbrot.createJobs(job_args)

    results=mlpr.executeBatch(jobs=jobs, compute_resource=compute_resource)

    X_list=[]
    for result0 in results:
        X0=np.load(mt.realizeFile(result0.outputs['output_npy']))
        X_list.append(X0)
    X = combine_subsampled_mandelbrot(X_list)
    return X

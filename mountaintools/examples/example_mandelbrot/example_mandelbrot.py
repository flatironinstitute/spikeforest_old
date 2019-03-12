
#%% Change working directory from the workspace root to the notebook file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
# This cell is needed for notebooks in vscode
import os
try:
	os.chdir(os.path.join(os.getcwd(), 'mountaintools/examples/example_mandelbrot'))
	print(os.getcwd())
except:
	pass

get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


#%%
# Import the MountainTools client
from mountaintools import client as mt
import mlprocessors as mlpr
mt.configLocal()

#%%
# Import the mandelbrot helpers from the mandelbrot/ directory
from mandelbrot import compute_mandelbrot, show_mandelbrot, combine_subsampled_mandelbrot, ComputeMandelbrot, compute_mandelbrot_parallel
import numpy as np

#%%
# Do a simple direct mandelbrot calculation
X = compute_mandelbrot(
    xmin=-2, xmax=0.5,
    ymin=-1.25, ymax=1.25,
    num_x=1000, num_iter=100
)

show_mandelbrot(X)

#%%

# Execute as a MountainTools processor (automatically caches results)
result = ComputeMandelbrot.execute(
    xmin=-2, xmax=0.5,
    ymin=-1.25, ymax=1.25,
    num_x=1000, num_iter=1000,
    output_npy=dict(ext='.npy', upload=True)
)

X = np.load(mt.realizeFile(result.outputs['output_npy']))

show_mandelbrot(X)

#%%

# Run in parallel by creating jobs that do subsampling
subsampling_factor=10

jobs = ComputeMandelbrot.createJobs([
    dict(
        xmin=-2, xmax=0.5,
        ymin=-1.25, ymax=1.25,
        num_x=1000, num_iter=10000,
        output_npy=dict(ext='.npy', upload=True),
        subsampling_factor=subsampling_factor,
        subsampling_offset=offset
    )
    for offset in range(0, subsampling_factor)
])

results = mlpr.executeBatch(jobs=jobs, num_workers=4)

X = combine_subsampled_mandelbrot([
    np.load(mt.realizeFile(result0.outputs['output_npy']))
    for result0 in results
])

show_mandelbrot(X)

#%%

# Run in parallel on remote compute resource

mt.login()
mt.configRemoteReadWrite(
    collection='fractal', share_id='fractal.share1'
)

subsampling_factor=80
jobs = ComputeMandelbrot.createJobs([
    dict(
        xmin=-2, xmax=0.5,
        ymin=-1.25, ymax=1.25,
        num_x=1000, num_iter=100000,
        output_npy=dict(ext='.npy', upload=True),
        subsampling_factor=subsampling_factor,
        subsampling_offset=offset
    )
    for offset in range(0, subsampling_factor)
])

results = mlpr.executeBatch(
    jobs=jobs,
    compute_resource = dict(
        resource_name='fractal-computer',
        collection='fractal',
        share_id='fractal.share1'
    )
)

X = combine_subsampled_mandelbrot([
    np.load(mt.realizeFile(result0.outputs['output_npy']))
    for result0 in results
])

show_mandelbrot(X)

#%%
# Select the compute resource,
# local or remote, depending on whether we are logged
# in to a remote system
# Note: if using local computer, start the compute resource via:
# bin/compute-resource-start local-computer --parallel 4

if (mode == 'local') or (mode == 'remote_readonly'):
    compute_resource=dict(
        resource_name='local-computer',
        collection='',
        share_id=''
    )
else:
    compute_resource=dict(
        resource_name='ccmlin008-80',
        collection='spikeforest',
        share_id='spikeforest.spikeforest2'
    )

#%%

# Run a batch with 80 jobs on the compute resource
# (high resolution, small number of iterations)

X=compute_mandelbrot_parallel(
    num_iter=300,  #50000,
    num_x=3000,
    num_parallel=8,
    compute_resource=compute_resource
)
show_mandelbrot(X)



#%%

# Run a batch with 80 jobs on the compute resource
# (high resolution, larger number of iterations)

X=compute_mandelbrot_parallel(
    num_iter=3000,  #50000,
    num_x=3000,
    num_parallel=80,
    compute_resource=compute_resource
)
show_mandelbrot(X)

#%%

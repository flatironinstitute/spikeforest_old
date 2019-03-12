
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

# Use one of the following three modes
mode='local'
# mode='remote_readonly'
# mode='remote_readwrite'

# Log in if you are authorized
if mode=='local':
    mt.configLocal()
elif mode=='remote_readonly':
    mt.configRemoteReadonly(collection='spikeforest', share_id='spikeforest.spikeforest2')
elif mode=='remote_readwrite':
    mt.login()
    mt.configRemoteReadWrite(collection='spikeforest', share_id='spikeforest.spikeforest2')
else:
    raise Exception('Invalid mode: '+mode)

#%%
# Import the mandelbrot helpers from the mandelbrot/ directory
from mandelbrot import compute_mandelbrot, show_mandelbrot, combine_subsampled_mandelbrot, ComputeMandelbrot, compute_mandelbrot_parallel
import numpy as np

#%%
# Do a simple direct mandelbrot calculation
X = compute_mandelbrot(xmin=-2, xmax=0.5, ymin=-1.25, ymax=1.25, num_x=1000, num_iter=100)
show_mandelbrot(X)

#%%
# Execute as a MountainTools processor (automatically caches results)
result=ComputeMandelbrot.execute(
    num_iter=1000,
    output_npy=dict(ext='.npy', upload=True)
)
X=np.load(mt.realizeFile(result.outputs['output_npy']))
show_mandelbrot(X)

#%%
# Run in parallel by creating jobs that do subsampling
subsampling_factor=4
jobs=[]
for offset in range(subsampling_factor):
    job0=ComputeMandelbrot.createJob(
        num_iter=10000,
        subsampling_factor=subsampling_factor,
        subsampling_offset=offset,
        output_npy=dict(ext='.npy', upload=True),
        _keep_temp_files=True
    )
    jobs.append(job0)

results=mlpr.executeBatch(jobs=jobs, num_workers=4)

X_list=[]
for result0 in results:
    X0=np.load(mt.realizeFile(result0.outputs['output_npy']))
    X_list.append(X0)
X = combine_subsampled_mandelbrot(X_list)

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

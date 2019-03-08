
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
# Import the MountainTools client and connect to a remote database
from mountaintools import client as mt
mt.configRemoteReadonly(collection='spikeforest', share_id='spikeforest.spikeforest2')

# Log in if you are authorized
login=True
if login:
    mt.login()
    mt.configRemoteReadWrite(collection='spikeforest', share_id='spikeforest.spikeforest2')
else:
    compute_resource=None

import mlprocessors as mlpr

#%%
# Import the mandelbrot helpers from the mandelbrot/ directory
import numpy as np
from matplotlib import pyplot as plt
from mandelbrot import compute_mandelbrot, show_mandelbrot, combine_subsampled_mandelbrot, ComputeMandelbrot, compute_mandelbrot_parallel

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
# Do a large computation on a REMOTE compute resource
compute_resource=dict(
    resource_name='ccmlin008-80',
    collection='spikeforest',
    share_id='spikeforest.spikeforest2'
)
X=compute_mandelbrot_parallel(
    num_iter=100000,
    num_x=3000,
    num_parallel=80,
    compute_resource=compute_resource
)
show_mandelbrot(X)



#%%
# Do 10x more iterations on a REMOTE compute resource
compute_resource=dict(
    resource_name='ccmlin008-80',
    collection='spikeforest',
    share_id='spikeforest.spikeforest2'
)
X=compute_mandelbrot_parallel(
    num_iter=100000*10,
    num_x=3000,
    num_parallel=80,
    compute_resource=compute_resource
)
show_mandelbrot(X)
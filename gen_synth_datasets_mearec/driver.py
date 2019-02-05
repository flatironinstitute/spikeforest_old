import os, sys
import numpy as np
from mountainlab_pytools import mlproc as mlp
from gen_synth_datasets import gen_synth_datasets

def main():
    #templates='kbucket://b5ecdf1474c5/MEArec/templates/templates_30_Neuronexus-32.h5'
    templates='kbucket://b5ecdf1474c5/MEArec/templates/templates_30_tetrode_mea.h5'
    K=15

    datasets=[]
    ds0=dict(
        duration=600,
        noise_level=12,
        templates=templates,
        n_exc=int(K/2), n_inh=K-int(K/2),
        f_exc=2, f_inh=7,
        min_rate=0.5,
        st_exc=1, st_inh=3,
        channel_ids=None,
        min_dist=15
    )
    num_datasets=10

    for j in range(1,num_datasets+1):
        ds=dict(        
            name='{}_synth'.format('{0:03d}'.format(j)),
            seed=j
        )
        for key in ds0:
            ds[key]=ds0[key]
        datasets.append(ds)

    print('DATASETS:')
    for ds in datasets:
        print(ds['name'])

    P=mlp.initPipeline()

    with P:
        gen_synth_datasets(datasets,tmpdir='tmp',outdir='datasets')
    
if __name__ == "__main__":
    main()
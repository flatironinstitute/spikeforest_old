import numpy as np
import json
import sys, os

parent_path=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_path+'/../mountainsort/packages/pyms')

from mountainlab_pytools import mdaio

processor_name='ms4alg.create_label_map'
processor_version='0.11.1'

def compute_templates_helper(*,timeseries,firings,clip_size=100):
    X=DiskReadMda(timeseries)
    M,N = X.N1(),X.N2()
    N=N
    F=mdaio.readmda(firings)
    L=F.shape[1]
    L=L
    T=clip_size
    times=F[1,:]
    labels=F[2,:].astype(int)
    K=np.max(labels)
    compute_templates._sums=np.zeros((M,T,K))
    compute_templates._counts=np.zeros(K)
    def _kernel(chunk,info):
        inds=np.where((info.t1<=times)&(times<=info.t2))[0]
        times0=(times[inds]-info.t1+info.t1a).astype(np.int32)
        labels0=labels[inds]
        
        clips0=np.zeros((M,clip_size,len(inds)),dtype=np.float32,order='F');
        cpp.extract_clips(clips0,chunk,times0,clip_size)
        
        for k in range(1,K+1):
            inds_kk=np.where(labels0==k)[0]
            compute_templates._sums[:,:,k-1]=compute_templates._sums[:,:,k-1]+np.sum(clips0[:,:,inds_kk],axis=2)
            compute_templates._counts[k-1]=compute_templates._counts[k-1]+len(inds_kk)
        return True
    TCR=TimeseriesChunkReader(chunk_size_mb=40, overlap_size=clip_size*2)
    if not TCR.run(timeseries,_kernel):
        return None
    templates=np.zeros((M,T,K))
    for k in range(1,K+1):
        if compute_templates._counts[k-1]:
            templates[:,:,k-1]=compute_templates._sums[:,:,k-1]/compute_templates._counts[k-1]
    return templates

def extract_clips_helper(*,timeseries,times,clip_size=100,verbose=False):
    X=mdaio.DiskReadMda(timeseries)
    M,N = X.N1(),X.N2()
    L=times.size
    T=clip_size
    extract_clips_helper._clips=np.zeros((M,T,L))
    def _kernel(chunk,info):
        inds=np.where((info.t1<=times)&(times<=info.t2))[0]
        times0=times[inds]-info.t1+info.t1a
        clips0=np.zeros((M,clip_size,len(inds)),dtype=np.float32,order='F');
        cpp.extract_clips(clips0,chunk,times0,clip_size)
        
        extract_clips_helper._clips[:,:,inds]=clips0
        return True
    TCR=TimeseriesChunkReader(chunk_size_mb=100, overlap_size=clip_size*2, verbose=verbose)
    if not TCR.run(timeseries,_kernel):
        return None
    return extract_clips_helper._clips



def create_label_map(*, metrics, label_map_out, firing_rate_thresh = .05, isolation_thresh = 0.95, noise_overlap_thresh = .03, peak_snr_thresh=1.5):
    """
    Generate a label map based on the metrics file, where labels being mapped to zero are to be removed.

    Parameters
    ----------
    metrics : INPUT
        Path of metrics json file to be used for generating the label map
    label_map_out : OUTPUT
        Path to mda file where the second column is the present label, and the first column is the new label
        ...
    firing_rate_thresh : float64
        (Optional) firing rate must be above this
    isolation_thresh : float64
        (Optional) isolation must be above this
    noise_overlap_thresh : float64
        (Optional) noise_overlap_thresh must be below this
    peak_snr_thresh : float64
        (Optional) peak snr must be above this
    """
    #TODO: Way to pass in logic or thresholds flexibly

    label_map = []

    #Load json
    with open(metrics) as metrics_json:
        metrics_data = json.load(metrics_json)

    #Iterate through all clusters
    for idx in range(len(metrics_data['clusters'])):
        if metrics_data['clusters'][idx]['metrics']['firing_rate'] < firing_rate_thresh or \
            metrics_data['clusters'][idx]['metrics']['isolation'] < isolation_thresh or \
            metrics_data['clusters'][idx]['metrics']['noise_overlap'] > noise_overlap_thresh or \
            metrics_data['clusters'][idx]['metrics']['peak_snr'] < peak_snr_thresh:
            #Map to zero (mask out)
            label_map.append([0,metrics_data['clusters'][idx]['label']])
        elif metrics_data['clusters'][idx]['metrics']['bursting_parent']: #Check if burst parent exists
            label_map.append([metrics_data['clusters'][idx]['metrics']['bursting_parent'],
                              metrics_data['clusters'][idx]['label']])
        else:
            label_map.append([metrics_data['clusters'][idx]['label'],
                              metrics_data['clusters'][idx]['label']]) # otherwise, map to itself!
                

    #Writeout
    return mdaio.writemda64(np.array(label_map),label_map_out)

create_label_map.name = processor_name
create_label_map.version = processor_version
create_label_map.author = 'J Chung and J Magland'
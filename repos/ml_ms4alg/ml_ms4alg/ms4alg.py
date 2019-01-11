import numpy as np
import isosplit5
from mountainlab_pytools import mdaio
import sys
import os
import multiprocessing
import datetime

# import h5py
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)
import h5py
warnings.resetwarnings()

def detect_on_channel(data,*,detect_threshold,detect_interval,detect_sign,margin=0):
    # Adjust the data to accommodate the detect_sign
    # After this adjustment, we only need to look for positive peaks
    if detect_sign<0:
        data=data*(-1)
    elif detect_sign==0:
        data=np.abs(data)
    elif detect_sign>0:
        pass

    data=data.ravel()
        
    #An event at timepoint t is flagged if the following two criteria are met:
    # 1. The value at t is greater than the detection threshold (detect_threshold)
    # 2. The value at t is greater than the value at any other timepoint within plus or minus <detect_interval> samples
    
    # First split the data into segments of size detect_interval (don't worry about timepoints left over, we assume we have padding)
    N=len(data)
    S2=int(np.floor(N/detect_interval))
    N2=S2*detect_interval
    data2=np.reshape(data[0:N2],(S2,detect_interval))
    
    # Find the maximum on each segment (these are the initial candidates)
    max_inds2=np.argmax(data2,axis=1)
    max_inds=max_inds2+detect_interval*np.arange(0,S2)
    max_vals=data[max_inds]
    
    # The following two tests compare the values of the candidates with the values of the neighbor candidates
    # If they are too close together, then discard the one that is smaller by setting its value to -1
    # Actually, this doesn't strictly satisfy the above criteria but it is close
    # TODO: fix the subtlety
    max_vals[ np.where((max_inds[0:-1]>=max_inds[1:]-detect_interval) & (max_vals[0:-1]<max_vals[1:]))[0] ]=-1
    max_vals[1+np.array( np.where((max_inds[1:]<=max_inds[0:-1]+detect_interval) & (max_vals[1:]<=max_vals[0:-1]))[0] )]=-1
    
    # Finally we use only the candidates that satisfy the detect_threshold condition
    times=max_inds[ np.where(max_vals>=detect_threshold)[0] ]
    if margin>0:
        times=times[np.where((times>=margin)&(times<N-margin))[0]]

    return times

def get_channel_neighborhood(m,Geom,*,adjacency_radius):
    M=Geom.shape[0]
    if adjacency_radius<0:
        return np.arange(M)
    deltas=Geom-np.tile(Geom[m,:],(M,1))
    distsqrs=np.sum(deltas**2,axis=1)
    inds=np.where(distsqrs<=adjacency_radius**2)[0]
    inds=np.sort(inds)
    return inds.ravel()

def subsample_array(X,max_num):
    if X.size==0:
        return X
    if max_num>=len(X):
        return X
    inds=np.random.choice(len(X), max_num, replace=False)
    return X[inds]

def compute_principal_components(X,num_components):
    u,s,vt=np.linalg.svd(X)
    u=u[:,:num_components]
    return u

def compute_templates_from_clips_and_labels(clips,labels):
    M=clips.shape[0]
    clip_size=clips.shape[1]
    K=int(np.max(labels))
    clip_sums=np.zeros((M,clip_size,K),dtype='float64')
    clip_counts=np.zeros((K),dtype='float64')
    for k in range(1,K+1):
        inds_k=np.where(labels==k)[0]
        if len(inds_k)>0:
            clip_counts[k-1]+=len(inds_k)
            clip_sums[:,:,k-1]+=np.sum(clips[:,:,inds_k],axis=2).reshape((M,clip_size))
            
    templates=np.zeros((M,clip_size,K))
    for k in range(1,K+1):
        if clip_counts[k-1]:
            templates[:,:,k-1]=clip_sums[:,:,k-1]/clip_counts[k-1]
    return templates

def compute_template_channel_peaks(templates,*,detect_sign):
    if detect_sign<0:
        templates=templates*(-1)
    elif detect_sign==0:
        templates=np.abs(templates)
    else:
        pass
    tc_peaks=np.max(templates,axis=1)
    tc_peak_times=np.argmax(templates,axis=1)
    return tc_peaks, tc_peak_times

def compute_sliding_maximum(X,radius):
    N=len(X)
    ret=np.zeros((N))
    for dt in range(-radius,radius+1):
        ret=np.maximum(ret,np.roll(X,dt))
    return ret

def extract_clips(data,*,times,clip_size):
    M=data.shape[0]
    T=clip_size
    L=len(times)
    Tmid = int(np.floor((T + 1) / 2) - 1);
    clips=np.zeros((M,T,L),dtype='float32')
    for j in range(L):
        t1=times[j]-Tmid
        t2=t1+clip_size
        clips[:,:,j]=data[:,t1:t2]
    return clips

def remove_zero_features(X):
    maxvals=np.max(np.abs(X),axis=1)
    features_to_use=np.where(maxvals>0)[0]
    return X[features_to_use,:]

def cluster(features,*,npca):
    num_events_for_pca=np.minimum(features.shape[1],1000)
    subsample_inds=np.random.choice(features.shape[1], num_events_for_pca, replace=False)
    u,s,vt=np.linalg.svd(features[:,subsample_inds])
    features2=(u.transpose())[0:npca,:]@features
    features2=remove_zero_features(features2)
    labels=isosplit5.isosplit5(features2)
    return labels

def branch_cluster(features,*,branch_depth=2,npca=10):
    if features.size == 0:
        return np.array([])

    min_size_to_try_split=20
    labels1=cluster(features,npca=npca).ravel().astype('int64')
    if np.min(labels1)<0:
        tmp_fname='/tmp/isosplit5-debug-features.mda'
        mdaio.writemda32(features,tmp_fname)
        raise Exception('Unexpected error in isosplit5. Features written to {}'.format(tmp_fname))
    K=int(np.max(labels1))
    if K<=1 or branch_depth<=1:
        return labels1
    label_offset=0
    labels_new=np.zeros(labels1.shape,dtype='int64')
    for k in range(1,K+1):
        inds_k=np.where(labels1==k)[0]
        if len(inds_k)>min_size_to_try_split:
            labels_k=branch_cluster(features[:,inds_k],branch_depth=branch_depth-1,npca=npca)
            K_k=int(np.max(labels_k))
            labels_new[inds_k]=label_offset+labels_k
            label_offset+=K_k
        else:
            labels_new[inds_k]=label_offset+1
            label_offset+=1
    return labels_new

def write_firings_file(channels,times,labels,fname):
    L=len(channels)
    X=np.zeros((3,L),dtype='float64')
    X[0,:]=channels
    X[1,:]=times
    X[2,:]=labels
    mdaio.writemda64(X,fname)

def detect_on_neighborhood_from_timeseries_model(X,*,channel,nbhd_channels,detect_threshold,detect_sign,detect_interval,margin,chunk_infos):
    N=X.numTimepoints()
    channel_rel=np.where(nbhd_channels==channel)[0][0] # The relative index of the central channel in the neighborhood

    times_list=[] # accumulate list of event times (one for each chunk)
    assign_to_this_neighborhood_list=[] # accumulate list of assign_to_this_neighborhood lists (one for each chunk)

    padding=detect_interval*10

    for ii in range(len(chunk_infos)):
        chunk0=chunk_infos[ii]
        X0=X.getChunk(t1=chunk0['t1']-padding,t2=chunk0['t2']+padding,channels=nbhd_channels)
        if detect_sign<0:
            X0*=-1
        elif detect_sign==0:
            X0=np.abs(X0)
        else:
            pass        
        times0 = detect_on_channel( X0[channel_rel,:].ravel(), detect_threshold=detect_threshold, detect_sign=1, detect_interval=detect_interval,margin=0)
        times0=times0[np.where((0<=times0-padding)&(times0-padding<chunk0['t2']-chunk0['t1']))[0]]
        vals=X0[channel_rel,times0]
        nearby_neighborhood_maximum0=compute_sliding_maximum(np.max(X0,axis=0).ravel(),radius=detect_interval)
        assign_to_this_neighborhood0=(vals==nearby_neighborhood_maximum0[times0])
        times_list.append(times0-padding+chunk0['t1'])
        assign_to_this_neighborhood_list.append(assign_to_this_neighborhood0)

    times=np.concatenate(times_list)
    assign_to_this_neighborhood=np.concatenate(assign_to_this_neighborhood_list)

    return times,assign_to_this_neighborhood

'''
def extract_clips_from_timeseries_model(X,times,*,clip_size,nbhd_channels):
    M=len(nbhd_channels)
    L=len(times)
    T=clip_size
    Tmid=int(np.floor((T + 1) / 2) - 1);
    clips=np.zeros((M,T,L))
    for ii in range(L):
        clips[:,:,ii]=X.getChunk(channels=nbhd_channels,t1=times[ii]-Tmid,t2=times[ii]-Tmid+T)
    return clips
'''

def compute_event_features_from_timeseries_model(X,times,*,nbhd_channels,clip_size,max_num_clips_for_pca,num_features,chunk_infos):
    if times.size == 0:
        return np.array([]) 

    N=X.numTimepoints()
    #X_neigh=X.getChunk(t1=0,t2=N,channels=nbhd_channels)
    M_neigh=len(nbhd_channels)

    padding=clip_size*10

    # Subsample and extract clips for pca
    times_for_pca=subsample_array(times,max_num_clips_for_pca)
    #clips_for_pca=extract_clips_from_timeseries_model(X,times_for_pca,clip_size=clip_size,nbhd_channels=nbhd_channels)
    clips_for_pca=np.zeros((M_neigh,clip_size,len(times_for_pca)))
    for ii in range(len(chunk_infos)):
        chunk0=chunk_infos[ii]
        inds0=np.where((chunk0['t1']<=times_for_pca)&(times_for_pca<chunk0['t2']))[0]
        if len(inds0)>0:
            X0=X.getChunk(t1=chunk0['t1']-padding,t2=chunk0['t2']+padding,channels=nbhd_channels)
            times0=times_for_pca[inds0]
            clips0=extract_clips(X0,times=times0-(chunk0['t1']-padding),clip_size=clip_size)
            clips_for_pca[:,:,inds0]=clips0

    # Compute the principal components
    # use twice as many features, because of branch method
    principal_components=compute_principal_components(clips_for_pca.reshape((M_neigh*clip_size,len(times_for_pca))),num_features*2) # (MT x 2F)

    # Compute the features for all the clips
    features=np.zeros((num_features*2,len(times)))
    for ii in range(len(chunk_infos)):
        chunk0=chunk_infos[ii]
        X0=X.getChunk(t1=chunk0['t1']-padding,t2=chunk0['t2']+padding,channels=nbhd_channels)
        inds0=np.where((chunk0['t1']<=times)&(times<chunk0['t2']))[0]
        times0=times[inds0]
        clips0=extract_clips(X0,times=times0-(chunk0['t1']-padding),clip_size=clip_size)
        features0=principal_components.transpose() @ clips0.reshape((M_neigh*clip_size,len(times0))) # (2F x MT) @ (MT x L0) -> (2F x L0)   
        features[:,inds0]=features0

    return features

    #clips_for_pca=extract_clips(X_neigh,times_for_pca,clip_size) # (MxTxL0)
    #clips_for_pca=clips_for_pca.reshape((M_neigh*clip_size,len(times_for_pca))) # vectorized (MT x L0)


    #all_clips=extract_clips(X_neigh,times,clip_size) # (MxTxL)
    #features=principal_components.transpose() @ all_clips.reshape((M_neigh*clip_size,len(times))) # (F x MT) @ (MT x L) -> (F x L)
    #return features

def compute_templates_from_timeseries_model(X,times,labels,*,nbhd_channels,clip_size,chunk_infos):
    # TODO: subsample smartly here
    padding=clip_size*10
    M0=len(nbhd_channels)
    K=np.max(labels) if labels.size > 0 else 0
    template_sums=np.zeros((M0,clip_size,K),dtype='float64')
    template_counts=np.zeros(K,dtype='float64')
    for ii in range(len(chunk_infos)):
        chunk0=chunk_infos[ii]
        X0=X.getChunk(t1=chunk0['t1']-padding,t2=chunk0['t2']+padding,channels=nbhd_channels)
        inds0=np.where((chunk0['t1']<=times)&(times<chunk0['t2']))[0]
        times0=times[inds0]
        labels0=labels[inds0]
        clips0=extract_clips(X0,times=times0-(chunk0['t1']-padding),clip_size=clip_size)

        for k in range(K):
            inds_k=np.where(labels0==(k+1))[0]
            if len(inds_k)>0:
                template_counts[k]+=len(inds_k)
                template_sums[:,:,k]+=np.sum(clips0[:,:,inds_k],axis=2).reshape((M0,clip_size))

    templates=np.zeros((M0,clip_size,K))
    for k in range(K):
        if template_counts[k]:
            templates[:,:,k]=template_sums[:,:,k]/template_counts[k]
    return templates    
    #N=X.numTimepoints()
    #X_neigh=X.getChunk(t1=0,t2=N,channels=nbhd_channels)
    #M_neigh=len(nbhd_channels)

    #all_clips=extract_clips(X_neigh,times,clip_size) # (MxTxL)
    #templates=compute_templates_from_clips_and_labels(all_clips,labels)
    #return templates

def create_chunk_infos(*,N,chunk_size):
    chunk_infos=[]
    num_chunks=int(np.ceil(N/chunk_size))
    for i in range(num_chunks):
        chunk={
            't1':i*chunk_size,
            't2':np.minimum(N,(i+1)*chunk_size)
        }
        chunk_infos.append(chunk)
    return chunk_infos

class _NeighborhoodSorter:
    def __init__(self):
        self._sorting_opts=None
        self._timeseries_model=None
        self._geom=None
        self._central_channel=None
        self._hdf5_path=None
        self._num_assigned_event_time_arrays=0
    def setSortingOpts(self,opts):
        self._sorting_opts=opts
    def setTimeseriesModel(self,model):
        self._timeseries_model=model
    def setHdf5FilePath(self,path):
        self._hdf5_path=path
    def setGeom(self,geom):
        self._geom=geom
    def setCentralChannel(self,m):
        self._central_channel=m
    def getPhase1Times(self):
        with h5py.File(self._hdf5_path,"r") as f:
            return np.array(f.get('phase1-times'))
    def getPhase1ChannelAssignments(self):
        with h5py.File(self._hdf5_path,"r") as f:
            return np.array(f.get('phase1-channel-assignments'))
    def getPhase2Times(self):
        with h5py.File(self._hdf5_path,"r") as f:
            return np.array(f.get('phase2-times'))
    def getPhase2Labels(self):
        with h5py.File(self._hdf5_path,"r") as f:
            return np.array(f.get('phase2-labels'))
    def addAssignedEventTimes(self,times):
        with h5py.File(self._hdf5_path,"a") as f:
            f.create_dataset('assigned-event-times-{}'.format(self._num_assigned_event_time_arrays),data=times)
            self._num_assigned_event_time_arrays+=1
    def runPhase1Sort(self):
        self.runSort(mode='phase1')
    def runPhase2Sort(self):
        self.runSort(mode='phase2')
    def runSort(self,*,mode):
        X=self._timeseries_model
        M_global=X.numChannels()
        N=X.numTimepoints()
        o=self._sorting_opts
        m_central=self._central_channel
        clip_size=o['clip_size']
        detect_interval=o['detect_interval']
        detect_sign=o['detect_sign']
        detect_threshold=o['detect_threshold']
        num_features=10 # TODO: make this a sorting opt
        geom=self._geom
        if geom is None:
            geom=np.zeros((M_global,2))

        chunk_infos=create_chunk_infos(N=N,chunk_size=100000)
        #chunk_infos=create_chunk_infos(N=N,chunk_size=10000000)

        nbhd_channels=get_channel_neighborhood(m_central,geom,adjacency_radius=o['adjacency_radius'])
        M_neigh=len(nbhd_channels)
        m_central_rel=np.where(nbhd_channels==m_central)[0][0]
        
        ## TODO: remove this
        #X_neigh=X.getChunk(t1=0,t2=N,channels=nbhd_channels)

        print('Neighboorhood of channel {} has {} channels.'.format(m_central,M_neigh))

        if mode=='phase1':
            print ('Detecting events on channel {} ({})...'.format(m_central+1,mode)); sys.stdout.flush()
            timer = datetime.datetime.now() 
            times,assign_to_this_neighborhood=detect_on_neighborhood_from_timeseries_model(X,channel=m_central,nbhd_channels=nbhd_channels,detect_threshold=detect_threshold,detect_sign=detect_sign,detect_interval=detect_interval,margin=clip_size,chunk_infos=chunk_infos)
            print('Elapsed time for detect on neighborhood:',datetime.datetime.now()-timer)
            print ('Num events detected on channel {} ({}): {}'.format(m_central+1,mode,len(times))); sys.stdout.flush()
        else:
            list=[]
            with h5py.File(self._hdf5_path,"r") as f:
                for ii in range(self._num_assigned_event_time_arrays):
                    list.append(np.array(f.get('assigned-event-times-{}'.format(ii))))
            times=np.concatenate(list) if list else np.array([])

        print ('Computing PCA features for channel {} ({})...'.format(m_central+1,mode)); sys.stdout.flush()
        max_num_clips_for_pca=1000 # TODO: this should be a setting somewhere
        # Note: we use twice as many features, because of branch method (MT x F)

        ## It is possible that a small number of events are duplicates (not exactly sure why)
        ## Let's eliminate those
        if len(times)!=len(np.unique(times)):
            print('WARNING: found {} of {} duplicate events for channel {} in {}'.format(len(times)-len(np.unique(times)),len(times),self._central_channel,mode))
            times=np.unique(times)
        else:
            if mode=='phase2':
                print('No duplicate events found for channel {} in {}'.format(self._central_channel,mode))
        #times=np.sort(times)
        features = compute_event_features_from_timeseries_model(X,times,nbhd_channels=nbhd_channels,clip_size=clip_size,max_num_clips_for_pca=max_num_clips_for_pca,num_features=num_features*2,chunk_infos=chunk_infos)
        
        # The clustering
        print ('Clustering for channel {} ({})...'.format(m_central+1,mode)); sys.stdout.flush()
        labels=branch_cluster(features,branch_depth=2,npca=num_features)
        K=np.max(labels) if labels.size > 0 else 0
        print ('Found {} clusters for channel {} ({})...'.format(K,m_central+1,mode)); sys.stdout.flush()
        
        if mode=='phase1':
            print ('Computing templates for channel {} ({})...'.format(m_central+1,mode)); sys.stdout.flush()
            templates=compute_templates_from_timeseries_model(X,times,labels,nbhd_channels=nbhd_channels,clip_size=clip_size,chunk_infos=chunk_infos)
            #mdaio.writemda32(templates,'tmp-templates-{}.mda'.format(m_central+1))

            print ('Re-assigning events for channel {} ({})...'.format(m_central+1,mode)); sys.stdout.flush()
            tc_peaks, tc_peak_times=compute_template_channel_peaks(templates,detect_sign=detect_sign) # M_neigh x K
            peak_channels=np.argmax(tc_peaks,axis=0) # The channels on which the peaks occur
            
            # make channel assignments and offset times
            inds2=np.where(assign_to_this_neighborhood)[0]
            times2=times[inds2]
            labels2=labels[inds2]
            channel_assignments2=np.zeros(len(times2))
            for k in range(K):
                assigned_channel_within_neighborhood=peak_channels[k]
                dt=tc_peak_times[assigned_channel_within_neighborhood][k]-tc_peak_times[m_central_rel][k]
                inds_k=np.where(labels2==(k+1))[0]
                if len(inds_k)>0:
                    times2[inds_k]+=dt
                    channel_assignments2[inds_k]=nbhd_channels[assigned_channel_within_neighborhood]
                    if m_central!=nbhd_channels[assigned_channel_within_neighborhood]:
                        print ('Re-assigning {} events from {} to {} with dt={} (k={})'.format(len(inds_k),m_central+1,nbhd_channels[assigned_channel_within_neighborhood]+1,dt,k+1)); sys.stdout.flush()
            with h5py.File(self._hdf5_path,"a") as f:
                f.create_dataset('phase1-times',data=times2)
                f.create_dataset('phase1-channel-assignments',data=channel_assignments2)
        elif mode=='phase2':
            with h5py.File(self._hdf5_path,"a") as f:
                f.create_dataset('phase2-times',data=times)
                f.create_dataset('phase2-labels',data=labels)
    
class TimeseriesModel_InMemory:
    def __init__(self,path):
        self._timeseries_path=path
        self._timeseries=mdaio.readmda(path)
    def numChannels(self):
        return self._timeseries.shape[0]
    def numTimepoints(self):
        return self._timeseries.shape[1]
    def getChunk(self,*,t1,t2,channels):
        if (t1<0) or (t2>self.numTimepoints()):
            ret=np.zeros((len(channels),t2-t1))
            t1a=np.maximum(t1,0)
            t2a=np.minimum(t2,self.numTimepoints())
            ret[:,t1a-(t1):t2a-(t1)]=self.getChunk(t1=t1a,t2=t2a,channels=channels)
            return ret
        else:
            return self._timeseries[np.array(channels),t1:t2]

class TimeseriesModel_Hdf5:
    def __init__(self,path):
        self._hdf5_path=path
        with h5py.File(self._hdf5_path,"r") as f:
            self._num_chunks=np.array(f.get('num_chunks'))[0]
            self._chunk_size=np.array(f.get('chunk_size'))[0]
            self._padding=np.array(f.get('padding'))[0]
            self._num_channels=np.array(f.get('num_channels'))[0]
            self._num_timepoints=np.array(f.get('num_timepoints'))[0]
    def numChannels(self):
        return self._num_channels
    def numTimepoints(self):
        return self._num_timepoints
    def getChunk(self,*,t1,t2,channels):
        if (t1<0) or (t2>self.numTimepoints()):
            ret=np.zeros((len(channels),t2-t1))
            t1a=np.maximum(t1,0)
            t2a=np.minimum(t2,self.numTimepoints())
            ret[:,t1a-(t1):t2a-(t1)]=self.getChunk(t1=t1a,t2=t2a,channels=channels)
            return ret
        else:
            c1=int(t1/self._chunk_size)
            c2=int((t2-1)/self._chunk_size)
            ret=np.zeros((len(channels),t2-t1))
            with h5py.File(self._hdf5_path,"r") as f:
                for cc in range(c1,c2+1):
                    if cc==c1:
                        t1a=t1
                    else:
                        t1a=self._chunk_size*cc
                    if cc==c2:
                        t2a=t2
                    else:
                        t2a=self._chunk_size*(cc+1)
                    for ii in range(len(channels)):
                        m=channels[ii]
                        assert(cc>=0)
                        assert(cc<self._num_chunks)
                        str='part-{}-{}'.format(m,cc)
                        offset=self._chunk_size*cc-self._padding
                        ret[ii,t1a-t1:t2a-t1]=f[str][t1a-offset:t2a-offset]
            return ret

class TimeseriesModel_Recording:
    def __init__(self,recording):
        self._recording=recording
    def numChannels(self):
        return len(self._recording.getChannelIds())
    def numTimepoints(self):
        return self._recording.getNumFrames()
    def getChunk(self,*,t1,t2,channels):
        channel_ids=self._recording.getChannelIds()
        channels2=np.zeros(len(channels))
        for i in range(len(channels)):
            channels2[i]=channel_ids[int(channels[i])]
        if (t1<0) or (t2>self.numTimepoints()):
            ret=np.zeros((len(channels),t2-t1))
            t1a=np.maximum(t1,0)
            t2a=np.minimum(t2,self.numTimepoints())
            ret[:,t1a-(t1):t2a-(t1)]=self.getChunk(t1=t1a,t2=t2a,channels=channels)
            return ret
        else:
            return self._recording.getTraces(start_frame=t1,end_frame=t2,channel_ids=channels2)
    
def prepare_timeseries_hdf5_from_recording(recording,timeseries_hdf5_fname,*,chunk_size,padding):
    chunk_size_with_padding=chunk_size+2*padding
    with h5py.File(timeseries_hdf5_fname,"w") as f:
        M=len(recording.getChannelIds()) # Number of channels
        N=recording.getNumFrames() # Number of timepoints
        num_chunks=int(np.ceil(N/chunk_size))
        f.create_dataset('chunk_size',data=[chunk_size])
        f.create_dataset('num_chunks',data=[num_chunks])
        f.create_dataset('padding',data=[padding])
        f.create_dataset('num_channels',data=[M])
        f.create_dataset('num_timepoints',data=[N])
        for j in range(num_chunks):
            padded_chunk=np.zeros((M,chunk_size_with_padding),dtype=float) # fix dtype here
            t1=int(j*chunk_size) # first timepoint of the chunk
            t2=int(np.minimum(N,(t1+chunk_size))) # last timepoint of chunk (+1)
            s1=int(np.maximum(0,t1-padding)) # first timepoint including the padding
            s2=int(np.minimum(N,t2+padding)) # last timepoint (+1) including the padding
            
            # determine aa so that t1-s1+aa = padding
            # so, aa = padding-(t1-s1)
            aa = padding-(t1-s1)
            padded_chunk[:,aa:aa+s2-s1]=recording.getTraces(start_frame=s1,end_frame=s2) # Read the padded chunk

            for m in range(M):
                f.create_dataset('part-{}-{}'.format(m,j),data=padded_chunk[m,:].ravel())

def prepare_timeseries_hdf5(timeseries_fname,timeseries_hdf5_fname,*,chunk_size,padding):
    chunk_size_with_padding=chunk_size+2*padding
    with h5py.File(timeseries_hdf5_fname,"w") as f:
        X=mdaio.DiskReadMda(timeseries_fname)
        M=X.N1() # Number of channels
        N=X.N2() # Number of timepoints
        num_chunks=int(np.ceil(N/chunk_size))
        f.create_dataset('chunk_size',data=[chunk_size])
        f.create_dataset('num_chunks',data=[num_chunks])
        f.create_dataset('padding',data=[padding])
        f.create_dataset('num_channels',data=[M])
        f.create_dataset('num_timepoints',data=[N])
        for j in range(num_chunks):
            padded_chunk=np.zeros((X.N1(),chunk_size_with_padding),dtype=X.dt())    
            t1=int(j*chunk_size) # first timepoint of the chunk
            t2=int(np.minimum(X.N2(),(t1+chunk_size))) # last timepoint of chunk (+1)
            s1=int(np.maximum(0,t1-padding)) # first timepoint including the padding
            s2=int(np.minimum(X.N2(),t2+padding)) # last timepoint (+1) including the padding
            
            # determine aa so that t1-s1+aa = padding
            # so, aa = padding-(t1-s1)
            aa = padding-(t1-s1)
            padded_chunk[:,aa:aa+s2-s1]=X.readChunk(i1=0,N1=X.N1(),i2=s1,N2=s2-s1) # Read the padded chunk

            for m in range(M):
                f.create_dataset('part-{}-{}'.format(m,j),data=padded_chunk[m,:].ravel())

def run_phase1_sort(neighborhood_sorter):
    neighborhood_sorter.runPhase1Sort()
    
def run_phase2_sort(neighborhood_sorter):
    neighborhood_sorter.runPhase2Sort()

class MountainSort4:
    def __init__(self):
        self._sorting_opts={
            "adjacency_radius":-1,
            "detect_sign":None, #must be set explicitly
            "detect_interval":10,
            "detect_threshold":3,
        }
        self._timeseries_path=None
        self._firings_out_path=None
        self._geom=None
        self._temporary_directory=None
        self._num_workers=0
        self._recording=None
    def setSortingOpts(self,clip_size=None,adjacency_radius=None,detect_sign=None,detect_interval=None,detect_threshold=None):
        if clip_size is not None:
            self._sorting_opts['clip_size']=clip_size
        if adjacency_radius is not None:
            self._sorting_opts['adjacency_radius']=adjacency_radius
        if detect_sign is not None:
            self._sorting_opts['detect_sign']=detect_sign
        if detect_interval is not None:
            self._sorting_opts['detect_interval']=detect_interval
        if detect_threshold is not None:
            self._sorting_opts['detect_threshold']=detect_threshold
    def setRecording(self,recording):
        self._recording=recording
    def setTimeseriesPath(self,path):
        self._timeseries_path=path
    def setFiringsOutPath(self,path):
        self._firings_out_path=path
    def setNumWorkers(self,num_workers):
        self._num_workers=num_workers
    def setGeom(self,geom):
        self._geom=geom
    def setTemporaryDirectory(self,tempdir):
        self._temporary_directory=tempdir
    def eventTimesLabelsChannels(self):
        return (self._event_times, self._event_labels, self._event_labels)
    def sort(self):
        if not self._temporary_directory:
            raise Exception('Temporary directory not set.')

        num_workers=self._num_workers
        if num_workers<=0:
            num_workers=int((multiprocessing.cpu_count()+1)/2)

        print('Num. workers = {}'.format(num_workers))

        clip_size=self._sorting_opts['clip_size']

        temp_hdf5_path=self._temporary_directory+'/timeseries.hdf5'
        if os.path.exists(temp_hdf5_path):
            os.remove(temp_hdf5_path)
        hdf5_chunk_size=1000000
        hdf5_padding=clip_size*10
        print ('Preparing {}...'.format(temp_hdf5_path))
        if self._timeseries_path:
            prepare_timeseries_hdf5(self._timeseries_path,temp_hdf5_path,chunk_size=hdf5_chunk_size,padding=hdf5_padding)
            X=TimeseriesModel_Hdf5(temp_hdf5_path)
        else:
            prepare_timeseries_hdf5_from_recording(self._recording,temp_hdf5_path,chunk_size=hdf5_chunk_size,padding=hdf5_padding)
            #X=TimeseriesModel_Recording(self._recording)
            X=TimeseriesModel_Hdf5(temp_hdf5_path)
        
        #X=TimeseriesModel_InMemory(self._timeseries_path)
        
        M=X.numChannels()
        N=X.numTimepoints()

        print ('Preparing neighborhood sorters (M={}, N={})...'.format(M,N)); sys.stdout.flush()
        neighborhood_sorters=[]
        for m in range(M):
            NS=_NeighborhoodSorter()
            NS.setSortingOpts(self._sorting_opts)
            NS.setTimeseriesModel(X)
            NS.setGeom(self._geom)
            NS.setCentralChannel(m)
            fname0=self._temporary_directory+'/neighborhood-{}.hdf5'.format(m)
            if os.path.exists(fname0):
                os.remove(fname0)
            NS.setHdf5FilePath(fname0)
            neighborhood_sorters.append(NS)

        pool = multiprocessing.Pool(num_workers)
        pool.map(run_phase1_sort, neighborhood_sorters)
        pool.close()
        pool.join()
        #for m in range(M):
        #    print ('Running phase1 neighborhood sort for channel {} of {}...'.format(m+1,M)); sys.stdout.flush()
        #    neighborhood_sorters[m].runPhase1Sort()

        for m in range(M):
            times_m=neighborhood_sorters[m].getPhase1Times()
            channel_assignments_m=neighborhood_sorters[m].getPhase1ChannelAssignments()
            for m2 in range(M):
                inds_m_m2=np.where(channel_assignments_m==m2)[0]
                if len(inds_m_m2)>0:
                    neighborhood_sorters[m2].addAssignedEventTimes(times_m[inds_m_m2])

        pool = multiprocessing.Pool(num_workers)
        pool.map(run_phase2_sort, neighborhood_sorters) 
        pool.close()
        pool.join()
        #for m in range(M):
        #    print ('Running phase2 sort for channel {} of {}...'.format(m+1,M)); sys.stdout.flush()
        #    neighborhood_sorters[m].runPhase2Sort()

        print ('Preparing output...'); sys.stdout.flush()
        all_times_list=[]
        all_labels_list=[]
        all_channels_list=[]
        k_offset=0
        for m in range(M):
            labels=neighborhood_sorters[m].getPhase2Labels()
            all_times_list.append(neighborhood_sorters[m].getPhase2Times())
            all_labels_list.append(labels+k_offset)
            all_channels_list.append(np.ones(len(neighborhood_sorters[m].getPhase2Times()))*(m+1))
            k_offset+=np.max(labels) if labels.size > 0 else 0

        all_times=np.concatenate(all_times_list)
        all_labels=np.concatenate(all_labels_list)
        all_channels=np.concatenate(all_channels_list)

        sort_inds=np.argsort(all_times)
        all_times=all_times[sort_inds]
        all_labels=all_labels[sort_inds]
        all_channels=all_channels[sort_inds]

        self._event_times=all_times
        self._event_labels=all_labels
        self._event_channels=all_channels

        if self._firings_out_path is not None:
            print ('Writing firings file...'); sys.stdout.flush()
            write_firings_file(all_channels,all_times,all_labels,self._firings_out_path)

        print ('Done with ms4alg.'); sys.stdout.flush()


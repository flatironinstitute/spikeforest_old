from sklearn.neighbors import NearestNeighbors
import numpy as np

def compute_noise_overlap(recording,sorting,unit_ids):
    if unit_ids is None:
        unit_ids=sorting.getUnitIds()
    max_num_events=500
    clip_size=50
    ret=[]
    for unit in unit_ids:
        times=sorting.getUnitSpikeTrain(unit_id=unit)
        if len(times)>max_num_events:
            times=np.random.choice(times,size=max_num_events)
        Nc=len(times)
        min_time=np.min(times)
        max_time=np.max(times)
        times_control=np.random.choice(np.arange(min_time,max_time+1),size=Nc)
        clips=np.stack(recording.getSnippets(snippet_len=clip_size, reference_frames=times))
        
        clips_control=np.stack(recording.getSnippets(snippet_len=clip_size, reference_frames=times_control))
        template=np.mean(clips,axis=0)
        max_ind=np.unravel_index(np.argmax(np.abs(template)),template.shape)
        chmax=max_ind[0]
        tmax=max_ind[1]
        max_val=template[chmax,tmax]
        weighted_clips_control=np.zeros(clips_control.shape)
        weights=np.zeros(Nc)
        for j in range(Nc):
            clip0=clips_control[j,:,:]
            val0=clip0[chmax,tmax]
            weight0=val0*max_val
            weights[j]=weight0
            weighted_clips_control[j,:,:]=clip0*weight0
        noise_template=np.sum(weighted_clips_control,axis=0)
        noise_template=noise_template/np.sum(np.abs(noise_template))*np.sum(np.abs(template))
        
        for j in range(Nc):
            clips[j,:,:]=subtract_clip_component(clips[j,:,:],noise_template)
            clips_control[j,:,:]=subtract_clip_component(clips_control[j,:,:],noise_template)
            
        all_clips=np.concatenate([clips,clips_control],axis=0)
        M0=all_clips.shape[1]
        T0=all_clips.shape[2]
        num_features=10
        nknn=6
        all_features=compute_pca_features(all_clips.reshape((Nc*2,M0*T0)),num_features)
        
        distances,indices = NearestNeighbors(n_neighbors=nknn+1, algorithm='auto').fit(all_features.T).kneighbors()
        group_id=np.zeros((Nc*2))
        group_id[0:Nc]=1
        group_id[Nc:]=2
        num_match=0
        total=0
        for j in range(Nc*2):
            for k in range(1,nknn+1):
                ind=indices[j][k]
                if group_id[j]==group_id[ind]:
                    num_match=num_match+1
                total=total+1
        pct_match=num_match/total
        noise_overlap=1-pct_match
        ret.append(noise_overlap)
    return ret

def compute_pca_features(X,num_components):
    u,s,vt=np.linalg.svd(X)
    return u[:,:num_components].T

def subtract_clip_component(clip1,component):
    V1=clip1.flatten()
    V2=component.flatten()
    V1=V1-np.mean(V1)
    V2=V2-np.mean(V2)
    V1=V1-V2*np.dot(V1,V2)/np.dot(V2,V2)
    return V1.reshape(clip1.shape)

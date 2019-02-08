import numpy as np

def synthesize_timeseries(*,output_extractor,waveforms,waveforms_tcenter=None,noise_level=1,samplerate=30000,duration=60,waveform_upsamplefac=13):
    num_timepoints=np.int64(samplerate*duration)
    waveform_upsamplefac=int(waveform_upsamplefac)
    W=waveforms
    
    M,TT,K = W.shape[0],W.shape[1],W.shape[2]
    T=int(TT/waveform_upsamplefac)
    if waveforms_tcenter is None:
        Tmid=int(np.ceil((T+1)/2-1))
    else:
        Tmid=waveforms_tcenter
    
    N=num_timepoints
            
    X=np.random.randn(M,N)*noise_level

    unit_ids=output_extractor.getUnitIds()
    for k0 in unit_ids:
        waveform0=waveforms[:,:,k0-1]
        times0=output_extractor.getUnitSpikeTrain(unit_id=k0)
        for t0 in times0:
            amp0=1
            frac_offset=int(np.floor((t0-np.floor(t0))*waveform_upsamplefac))
            tstart=np.int64(np.floor(t0))-Tmid
            if (0<=tstart) and (tstart+T<=N):
                X[:,tstart:tstart+T]=X[:,tstart:tstart+T]+waveform0[:,frac_offset::waveform_upsamplefac]*amp0

    return X
from matplotlib import pyplot as plt
import numpy as np

class OutputVisualizer:
    '''A class that contains functions for visualizing the output of spike sorting.
    '''
    def __init__(self,input_extractor,output_extractor):
        self._IX=input_extractor
        self._OX=output_extractor

    def viewUnitWaveforms(self, units=None, channels=None):
        '''Plot average spike waveforms and representative spikes for a collection of units
        Parameters
        ----------
        units: list of ints
            A list of unit ids
        channels: list of ints
            A list of channel ids
        '''
        if units is None:
            units=self._OX.getUnitIds()
        M=self._IX.getNumChannels()
        channel_locations=np.zeros((M,2))
        for ch in range(M):
            loc=self._IX.getChannelInfo(ch)['location']
            channel_locations[ch,:]=loc[-2:]
        if channels is None:
            channels=range(M)
        
        list=[]
        for unit in units:
            spikes=self._get_random_spike_waveforms(unit=unit,max_num=50,channels=channels)
            item=dict(
                representative_waveforms=spikes,
                title='Unit {}'.format(unit)
            )
            list.append(item)
        with plt.rc_context({'axes.edgecolor':'gray'}):
            #self.plot_spike_shapes_multi(list,channel_locations=channel_locations[np.array(channels),:])
            self.plot_spike_shapes_multi(list,channel_locations=None)
    
    def viewAutoCorrelograms(self, units=None):
        '''Plot autocorrelograms for a collection of units
        Parameters
        ----------
        units: list of ints
            A list of unit ids
        '''
        if units is None:
            units=range(1,self._output_analyzer.getUnitCount()+1)
        if not units:
            return
        
        list=compute_autocorrelograms(self._output_analyzer,units=units,max_dt_msec=50,bin_size_msec=2)
        
        ncols=4
        nrows = np.ceil(len(list) / ncols)
        plt.figure(figsize=(3 * ncols, 3 * nrows))
        for i, A0 in enumerate(list):
            plt.subplot(nrows, ncols, i + 1)
            with plt.rc_context({'axes.edgecolor':'gray'}):
                wid=(A0['bin_edges'][1]-A0['bin_edges'][0])*1000
                plt.bar(left=A0['bin_edges'][0:-1]*1000,height=A0['bin_counts'],width=wid,color='gray')
                plt.xlabel('dt (msec)')
                plt.gca().get_yaxis().set_ticks([])
    
    def _get_random_spike_waveforms(self,*,unit,max_num,channels):
        st=self._OX.getUnitSpikeTrain(unit_id=unit)
        num_events=len(st)
        if num_events>max_num:
            event_indices=np.random.choice(range(num_events),size=max_num,replace=False)
        else:
            event_indices=range(num_events)
        spikes=self._IX.getRawSnippets(center_frames=st[event_indices],snippet_len=100,channel_ids=channels)
        spikes=np.dstack(tuple(spikes))
        return spikes
    
    def plot_spike_shapes(self, *, representative_waveforms=None, average_waveform=None, channel_locations=None, ylim=None, max_representatives=None, color='blue',title=''):
        if average_waveform is None:
            if representative_waveforms is None:
                raise Exception('You must provide either average_waveform, representative waveforms, or both')
            average_waveform=np.mean(representative_waveforms,axis=2)
        M=average_waveform.shape[0] # number of channels
        T=average_waveform.shape[1] # number of timepoints
        if ylim is None:
            ylim=[average_waveform.min(),average_waveform.max()]
        yrange=ylim[1]-ylim[0]
        if channel_locations is None:
            channel_locations=np.zeros((M,2))
            for m in range(M):
                channel_locations[m,:]=[0,-m]

        spacing=1/0.8 # TODO: auto-determine this from the channel_locations

        xvals=np.linspace(-yrange/2,yrange/2,T)
        if representative_waveforms is not None:
            if max_representatives is not None:
                W0=representative_waveforms
                if W0.shape[2]>max_representatives:
                    indices=np.random.choice(range(W0.shape[2]),size=max_representatives,replace=False)
                    representative_waveforms=W0[:,:,indices]
            L=representative_waveforms.shape[2]
            XX=np.zeros((T,M,L))
            YY=np.zeros((T,M,L))
            for m in range(M):
                loc=channel_locations[m,-2:]*yrange*spacing
                for j in range(L):
                    XX[:,m,j]=loc[0]+xvals
                    YY[:,m,j]=loc[1]+representative_waveforms[m,:,j]-representative_waveforms[m,0,j]
            XX=XX.reshape(T,M*L)
            YY=YY.reshape(T,M*L)
            plt.plot(XX, YY, color=(0.5,0.5,0.5), alpha=0.4)

            XX=np.zeros((T,M))
            YY=np.zeros((T,M))
            for m in range(M):
                loc=channel_locations[m,-2:]*yrange*spacing
                XX[:,m]=loc[0]+xvals
                YY[:,m]=loc[1]+average_waveform[m,:]-average_waveform[m,0]
            plt.plot(XX, YY, color)

        plt.gca().get_xaxis().set_ticks([])
        plt.gca().get_yaxis().set_ticks([])
        if title:
            plt.title(title,color='gray')

    def _get_ylim_for_item(self,average_waveform=None,representative_waveforms=None):
        if average_waveform is None:
            if representative_waveforms is None:
                raise Exception('You must provide either average_waveform, representative waveforms, or both')
            average_waveform=np.mean(representative_waveforms,axis=2)
        return [average_waveform.min(),average_waveform.max()]

    def _determine_global_ylim(self,list):
        ret=[0,0]
        for item in list:
            ylim0 = self._get_ylim_for_item(
                average_waveform=item.get('average_waveform',None),
                representative_waveforms=item.get('representative_waveforms',None)
            )
            ret[0]=np.minimum(ylim0[0],ret[0])
            ret[1]=np.maximum(ylim0[1],ret[1])
        return ret

    def plot_spike_shapes_multi(self, list, *, ncols=5, **kwargs):
        if 'ylim' in kwargs:
            ylim=kwargs['ylim']
        else:
            ylim=self._determine_global_ylim(list)
        nrows = np.ceil(len(list) / ncols)
        plt.figure(figsize=(3 * ncols, 3 * nrows))
        for i, item in enumerate(list):
            plt.subplot(nrows, ncols, i + 1)
            self.plot_spike_shapes(**item, **kwargs, ylim=ylim)


def compute_autocorrelogram(times,*,max_dt_tp,bin_size_tp,max_samples=None):
    num_bins_left=int(max_dt_tp/bin_size_tp) # number of bins to the left of the origin
    L=len(times) # number of events
    times2=np.sort(times) # the sorted times
    step=1 # This is the index step between an event and the next one to compare
    candidate_inds=np.arange(L) # These are the events we are going to consider
    if max_samples is not None:
        if len(candidate_inds)>max_samples:
            candidate_inds=np.random.choice(candidate_inds,size=max_samples,replace=False)
    vals_list=[] # A list of all offsets we have accumulated
    while True:
        candidate_inds=candidate_inds[candidate_inds+step<L] # we only consider events that are within workable range
        candidate_inds=candidate_inds[times2[candidate_inds+step]-times2[candidate_inds]<=max_dt_tp] # we only consider event-pairs that are within max_dt_tp apart
        if len(candidate_inds)>0: # if we have some events to consider
            vals=times2[candidate_inds+step]-times2[candidate_inds]
            vals_list.append(vals) # add to the autocorrelogram
            vals_list.append(-vals) # keep it symmetric
        else:
            break # no more to consider
        step+=1
    if len(vals_list)>0: # concatenate all the values
        all_vals=np.concatenate(vals_list)
    else:
        all_vals=np.array([]);
    aa=np.arange(-num_bins_left,num_bins_left+1)*bin_size_tp
    all_vals=np.sign(all_vals)*(np.abs(all_vals)-bin_size_tp*0.00001) # a trick to make the histogram symmetric due to differences in rounding for positive and negative, i suppose
    bin_counts,bin_edges=np.histogram(all_vals,bins=aa)
    return (bin_counts,bin_edges)

def compute_autocorrelograms(output_analyzer,*,units=None,max_dt_msec=50,bin_size_msec=2,max_samples=5000):
    samplerate=output_analyzer.sampleRate()
    if units is None:
        units=range(1,output_analyzer.getUnitCount()+1)
    max_dt_tp=max_dt_msec/1000*samplerate
    bin_size_tp=bin_size_msec/1000*samplerate
    ret=[]
    for unit in units:
        times=output_analyzer.getUnitEventTimes(unit=unit)
        bin_counts,bin_edges=compute_autocorrelogram(times,max_dt_tp=max_dt_tp,bin_size_tp=bin_size_tp,max_samples=max_samples)
        A=dict(
            unit=unit,
            bin_edges=bin_edges/samplerate,
            bin_counts=bin_counts
        )
        ret.append(A)
    return ret
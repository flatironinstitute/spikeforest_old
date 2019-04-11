# pylint: disable=no-member

import mlprocessors as mlpr
import spikeextractors as se
import h5py
import numpy as np
import spikeextractors as se
from mountaintools import client as mt
import mtlogging

class EfficientAccessRecordingExtractor(se.RecordingExtractor):
    def __init__(self, *, path=None, recording=None, _dest_path=None):
        se.RecordingExtractor.__init__(self)
        if path is not None:
            if recording is not None:
                raise Exception('Cannot pass both path and recording to EfficientAccessRecordingExtractor.')
            self._path = path
        elif recording is not None:
            if not hasattr(recording, 'hash'):
                try:
                    if not hasattr(recording, 'hash'):
                        print('''
                        Warning: Recording does not have the hash attribute.
                        Using sampling method to compute a hash.''')
                        setattr(recording, 'hash', _hash(recording))
                except:
                    raise Exception('Recording class does not support the sampling hash.')
            path0 = CreateEfficientAccessRecordingFile.execute(
                recording=recording,
                hdf5_out=dict(ext='.hdf5', dest_path=_dest_path)
            ).outputs['hdf5_out']
            self._path = mt.realizeFile(path=path0)
        else:
            raise Exception('Missing argument: path or recording')
        
        with h5py.File(self._path, "r") as f:
            self._num_segments = int(np.array(f.get('num_segments'))[0])
            self._segment_size = int(np.array(f.get('segment_size'))[0])
            self._num_channels = int(np.array(f.get('num_channels'))[0])
            self._channel_ids = np.array(f.get('channel_ids')).tolist()
            self._num_timepoints = int(np.array(f.get('num_timepoints'))[0])
            self._samplerate = np.array(f.get('samplerate'))[0]
            self._recording_hash = np.array(f.get('recording_hash'))[0].decode()
            assert type(self._recording_hash)==str
            geom = np.array(f.get('geom'))
            channel_locations = [geom[m, :].ravel() for m in range(self._num_channels)]
            self.setChannelLocations(channel_ids=self._channel_ids, locations=channel_locations)
    
    def hash(self):
        return self._recording_hash

    def path(self):
        return self._path
        
    def getChannelIds(self):
        return self._channel_ids

    def getNumFrames(self):
        return self._num_timepoints

    def getSamplingFrequency(self):
        return self._samplerate

    @mtlogging.log(name='EfficientAccessRecordingExtractor:getTraces')
    def getTraces(self, channel_ids=None, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = self.getNumFrames()
        if channel_ids is None:
            channel_ids = self.getChannelIds()
        
        t1 = int(start_frame)
        t2 = int(end_frame)
        c1 = int(t1/self._segment_size)
        c2 = int((t2-1)/self._segment_size)
        ret = np.zeros((len(channel_ids), t2-t1))
        with h5py.File(self._path,"r") as f:
            for cc in range(c1, c2+1):
                if cc==c1:
                    t1a=t1
                else:
                    t1a=self._segment_size*cc
                if cc==c2:
                    t2a=t2
                else:
                    t2a=self._segment_size*(cc+1)
                for ii, m in enumerate(channel_ids):
                    str0 = 'part-{}-{}'.format(m, cc)
                    offset = self._segment_size*cc
                    ret[ii, t1a-t1:t2a-t1] = f[str0][t1a-offset:t2a-offset]
        return ret
    
    @staticmethod
    def writeRecording(recording, save_path):
        EfficientAccessRecordingExtractor(recording=recording, _dest_path=save_path)

class CreateEfficientAccessRecordingFile(mlpr.Processor):
    NAME = 'CreateEfficientAccessRecordingFile'
    VERSION = '0.1.2'
    recording = mlpr.Input()
    segment_size = mlpr.IntegerParameter(optional=True, default=1000000)
    hdf5_out = mlpr.Output()
    
    def run(self):
        recording = self.recording
        segment_size = self.segment_size
        channel_ids = recording.getChannelIds()
        samplerate = recording.getSamplingFrequency()
        M = len(channel_ids) # number of channels
        N = recording.getNumFrames() # Number of timepoints
        num_segments = int(np.ceil(N/segment_size))
        
        channel_locations = recording.getChannelLocations(channel_ids = channel_ids)
        nd = len(channel_locations[0])
        geom = np.zeros((M, nd))
        for m in range(M):
            geom[m, :] = channel_locations[m]
            
        with h5py.File(self.hdf5_out, "w") as f:
            f.create_dataset('segment_size', data=[segment_size])
            f.create_dataset('num_segments', data=[num_segments])
            f.create_dataset('num_channels', data=[M])
            f.create_dataset('channel_ids', data=np.array(channel_ids))
            f.create_dataset('num_timepoints', data=[N])
            f.create_dataset('samplerate', data=[samplerate])
            f.create_dataset('geom', data=geom)
            if callable(recording.hash):
                hash0 = recording.hash()
            else:
                hash0 = recording.hash
            f.create_dataset('recording_hash', data=np.array([hash0.encode()]))
            for j in range(num_segments):
                segment = np.zeros((M,segment_size),dtype=float) # fix dtype here
                t1 = int(j*segment_size) # first timepoint of the segment
                t2 = int(np.minimum(N,(t1+segment_size))) # last timepoint of segment (+1)
                s1 = int(np.maximum(0,t1)) # first timepoint
                s2 = int(np.minimum(N,t2)) # last timepoint (+1)

                # determine aa so that t1-s1+aa = 0
                # so, aa = -(t1-s1)
                aa = -(t1-s1)
                segment[:,aa:aa+s2-s1] = recording.getTraces(start_frame=s1, end_frame=s2) # Read the segment

                for ii, ch in enumerate(channel_ids):
                    f.create_dataset('part-{}-{}'.format(ch, j), data=segment[ii,:].ravel())

def _hash(self):
    from mountaintools import client as mt
    obj = {
        'channels': tuple(self.getChannelIds()),
        'frames': self.getNumFrames(),
        'data': samplehash(self)
    }
    return mt.sha1OfObject(obj)
    
def samplehash(self):
    rng = np.random.RandomState(37)
    n_samples = min(self.getNumFrames()//1000, 100)
    inds = rng.randint(low=0, high=self.getNumFrames(), size=n_samples)
    h = 0
    for i in inds:
        t = self.getTraces(start_frame=i, end_frame=i+100)
        h = hash((hash(bytes(t)),hash(h)))
    return h


from .ms4alg import MountainSort4
import tempfile
import shutil
import spikeextractors as se
import numpy as np
import multiprocessing

def mountainsort4(*,recording,detect_sign,clip_size=50,adjacency_radius=-1,detect_threshold=3,detect_interval=10,num_workers=None):
  if num_workers is None:
    num_workers=int((multiprocessing.cpu_count()+1)/2)

  print('Using {} workers.'.format(num_workers))

  MS4=MountainSort4()
  MS4.setRecording(recording)
  geom=_get_geom_from_recording(recording)
  MS4.setGeom(geom)
  MS4.setSortingOpts(
    clip_size=clip_size,
    adjacency_radius=adjacency_radius,
    detect_sign=detect_sign,
    detect_interval=detect_interval,
    detect_threshold=detect_threshold
  )
  tmpdir = tempfile.mkdtemp()
  MS4.setNumWorkers(num_workers)
  print('Using tmpdir: '+tmpdir)
  MS4.setTemporaryDirectory(tmpdir)
  try:
    MS4.sort()
  except:
    print('Cleaning tmpdir:: '+tmpdir)
    shutil.rmtree(tmpdir)
    raise
  print('Cleaning tmpdir::::: '+tmpdir)
  shutil.rmtree(tmpdir)
  times,labels,channels=MS4.eventTimesLabelsChannels()
  output=se.NumpySortingExtractor()
  output.setTimesLabels(times=times,labels=labels)
  return output


def _get_geom_from_recording(recording):
  channel_ids=recording.getChannelIds()
  M=len(channel_ids)
  location0=recording.getChannelProperty(channel_ids[0],'location')
  nd=len(location0)
  geom=np.zeros((M,nd))
  for i in range(M):
    location_i=recording.getChannelProperty(channel_ids[i],'location')
    geom[i,:]=location_i
  return geom
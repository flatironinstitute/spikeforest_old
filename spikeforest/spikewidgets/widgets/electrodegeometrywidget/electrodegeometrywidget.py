from matplotlib import pyplot as plt
import numpy as np

class ElectrodeGeometryWidget:
  def __init__(self, *, recording):
    self._recording = recording

  def plot(self,width=1.5,height=1.5):
    self._do_plot(width=width,height=height)

  def _get_geom(self):
    RX=self._recording
    return np.stack([RX.getChannelProperty(channel_id=ch,property_name='location') for ch in RX.getChannelIds()])
    
  def _do_plot(self,width,height):
    R=self._recording
    geom=self._get_geom()
    
    fig = plt.figure(figsize=(width,height))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis('off')
    
    x=geom[:,0]
    y=geom[:,1]
    xmin=np.min(x); xmax=np.max(x)
    ymin=np.min(y); ymax=np.max(y)
    
    marker_size=width*fig.dpi/6
    margin=np.maximum(xmax-xmin,ymax-ymin)*0.2

    plt.scatter(x,y,marker='o', s=int(marker_size**2))
    plt.axis('equal')
    plt.xticks([])
    plt.yticks([])
    plt.xlim(xmin-margin,xmax+margin)
    plt.ylim(ymin-margin,ymax+margin)
    #plt.show()
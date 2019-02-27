from matplotlib import pyplot as plt
from PIL import Image
import os

def savePlot(fname,quality=40,close_figure=True):
    plt.savefig(fname+'.png')
    if close_figure:
      plt.close()
    im=Image.open(fname+'.png').convert('RGB')
    os.remove(fname+'.png')
    im.save(fname,quality=quality)
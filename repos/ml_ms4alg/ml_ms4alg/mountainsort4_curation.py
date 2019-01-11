import spikeextractors as se
from .compute_noise_overlap import compute_noise_overlap
import numpy as np

def mountainsort4_curation(*,recording,sorting,noise_overlap_threshold=None):
    if noise_overlap_threshold is not None:
        units=sorting.getUnitIds()
        noise_overlap_scores=compute_noise_overlap(recording=recording,sorting=sorting,unit_ids=units)
        inds=np.where(np.array(noise_overlap_scores)<=noise_overlap_threshold)[0]
        new_units=list(np.array(units)[inds])
        sorting=se.SubSortingExtractor(parent_sorting=sorting,unit_ids=new_units)
    return sorting
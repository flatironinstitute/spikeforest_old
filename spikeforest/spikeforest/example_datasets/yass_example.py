from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor, example_datasets
import numpy as np
import os

def yass_example(download=True, set_id=1):
    if set_id in range(1,7):
        dsdir = 'kbucket://15734439d8cf/groundtruth/visapy_mea/set{}'.format(set_id)
        IX = SFMdaRecordingExtractor(dataset_directory=dsdir, download=download)
        path1 = os.path.join(dsdir, 'firings_true.mda')
        print(path1)
        OX = SFMdaSortingExtractor(path1)
        return (IX, OX)
    else:
        raise Exception('Invalid ID for yass_example {} is not betewen 1..6'.format(set_id))

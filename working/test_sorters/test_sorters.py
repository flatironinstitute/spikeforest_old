#!/usr/bin/env python

from spikesorters import MountainSort4, SpykingCircus
from mountaintools import client as mt
import spikeforest_analysis as sa
import json
import numpy as np
import pytest

magland_synth_c4_recdir = 'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C4/001_synth'
magland_synth_c8_recdir = 'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C8/001_synth'
kampff1 = 'sha1dir://c86202ca09f303b6c6d761b94975054c29c85d2b.paired_kampff/kampff1'

@pytest.mark.spikeforest
@pytest.mark.ms4
@pytest.mark.exclude
def test_ms4():
    sorter = MountainSort4
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )

    # do_sorting_test(sorter, params, magland_synth_c4_recdir, assert_avg_accuracy=0.8)
    # do_sorting_test(sorter, params, magland_synth_c8_recdir, assert_avg_accuracy=0.8)
    # do_sorting_test(sorter, params, kampff1, assert_avg_accuracy=0.8) # jfm laptop: ~220 seconds

@pytest.mark.spikeforest
@pytest.mark.sc
@pytest.mark.exclude
def test_sc():
    sorter = SpykingCircus
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )

    # do_sorting_test(sorter, params, magland_synth_c4_recdir, assert_avg_accuracy=0.8)
    # do_sorting_test(sorter, params, magland_synth_c8_recdir, assert_avg_accuracy=0.8)
    do_sorting_test(sorter, params, kampff1, assert_avg_accuracy=0.8)

def do_sorting_test(sorting_processor, params, recording_dir, assert_avg_accuracy):
    mt.configDownloadFrom('spikeforest.kbucket')
    
    recdir = recording_dir
    mt.createSnapshot(path=recdir, download_recursive=True)
    sorting = sorter.execute(
        recording_dir = recdir,
        firings_out = {'ext': '.mda'},
        **params,
        _container='default',
        _force_run=True
    )

    comparison = sa.GenSortingComparisonTable.execute(
        firings=sorting.outputs['firings_out'],
        firings_true=recdir+'/firings_true.mda',
        units_true=[],
        json_out={'ext':'.json'},
        html_out={'ext':'.html'},
        _container='default',
        _force_run=True
    )

    X = mt.loadObject(path=comparison.outputs['json_out'])
    accuracies = [float(a['accuracy']) for a in X.values()]
    avg_accuracy = np.mean(accuracies)

    print('Average accuracy: {}'.format(avg_accuracy))

    assert(avg_accuracy>=assert_avg_accuracy)

if __name__ == "__main__":
    main()
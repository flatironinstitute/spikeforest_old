from spikesorters import MountainSort4, SpykingCircus, KiloSort, KiloSort2, IronClust, HerdingSpikes2, JRClust, Klusta
from mountaintools import client as mt
import spikeforest_analysis as sa
import json
import numpy as np
import pytest

synth_magland_c4_recdir = 'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C4/001_synth'
synth_magland_c8_recdir = 'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C8/001_synth'
kampff1_recdir = 'sha1dir://c86202ca09f303b6c6d761b94975054c29c85d2b.paired_kampff/kampff1'
neuropix32c_recdir = 'sha1dir://d446c8e74fc4ca3a0dab491fca6c10189b527709.neuropix32c.c14'
boyden32c_recdir = 'sha1dir://b28dbf52748dcb401034d1c353807bcbff20e106.boyden32c.1103_1_1'
sqmea64c_recdir = 'sha1dir://e8de6ac2138bf775f29f8ab214d04aa92e20ca79'
paired_mea64c_recdir = 'sha1dir://7f12606802ade3c7c71eb306490b7840eb8b1fb4.paired_mea64c'

@pytest.mark.spikeforest
@pytest.mark.ms4
@pytest.mark.exclude
def test_ms4():
    sorter = MountainSort4
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )

    # do_sorting_test(sorter, params, synth_magland_c4_recdir, assert_avg_accuracy=0.8)
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.8)
    # do_sorting_test(sorter, params, kampff1_recdir, assert_avg_accuracy=0.8) # jfm laptop: ~220 seconds


@pytest.mark.spikeforest
@pytest.mark.ms4_magland_c4
@pytest.mark.exclude
def test_ms4_magland_c4():
    sorter = MountainSort4
    params = dict(
        detect_sign=-1,
        adjacency_radius=75,
    )
    do_sorting_test(sorter, params, synth_magland_c4_recdir, assert_avg_accuracy=0.5)


@pytest.mark.spikeforest
@pytest.mark.ms4_magland_c8
@pytest.mark.exclude
def test_ms4_magland_c8():
    sorter = MountainSort4
    params = dict(
        detect_sign=-1,
        adjacency_radius=75,
    )
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.5)

    
@pytest.mark.spikeforest
@pytest.mark.ms4_neuropix32c
@pytest.mark.exclude
def test_ms4_neuropix32c():
    sorter = MountainSort4
    params = dict(
        detect_sign=-1,
        adjacency_radius=75,
    )
    do_sorting_test(sorter, params, neuropix32c_recdir, assert_avg_accuracy=0.5)


@pytest.mark.spikeforest
@pytest.mark.sc
@pytest.mark.exclude
def test_sc():
    sorter = SpykingCircus
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )

    # do_sorting_test(sorter, params, synth_magland_c4_recdir, assert_avg_accuracy=0.8)
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.8)
    # do_sorting_test(sorter, params, kampff1_recdir, assert_avg_accuracy=0.8)


@pytest.mark.spikeforest
@pytest.mark.ks2_magland_c4
@pytest.mark.exclude
def test_ks2_magland_c4():
    sorter = KiloSort2
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(sorter, params, synth_magland_c4_recdir, assert_avg_accuracy=0.8)


@pytest.mark.spikeforest
@pytest.mark.ks2_magland_c8
@pytest.mark.exclude
def test_ks2_magland_c8():
    sorter = KiloSort2
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.8)


@pytest.mark.spikeforest
@pytest.mark.klusta_magland_c4
@pytest.mark.exclude
def test_klusta_magland_c4():
    sorter = Klusta
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(sorter, params, synth_magland_c4_recdir, assert_avg_accuracy=0.8)


@pytest.mark.spikeforest
@pytest.mark.klusta_magland_c8
@pytest.mark.exclude
def test_klusta_magland_c8():
    sorter = Klusta
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.8)


@pytest.mark.spikeforest
@pytest.mark.hs2_magland_c8
@pytest.mark.exclude
def test_hs2_magland_c8():
    sorter = HerdingSpikes2
    params = dict()
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.1)


@pytest.mark.spikeforest
@pytest.mark.hs2_paired_mea64c
@pytest.mark.exclude
def test_hs2_paired_mea64c():
    sorter = HerdingSpikes2
    params = dict()
    do_sorting_test(sorter, params, paired_mea64c_recdir, assert_avg_accuracy=0.1, container=None)


@pytest.mark.spikeforest
@pytest.mark.hs2_neuropix32c
@pytest.mark.exclude
def test_hs2_neuropix32c():
    sorter = HerdingSpikes2
    params = dict(
        adjacency_radius=50,
    )
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.1)


@pytest.mark.spikeforest
@pytest.mark.hs2_boyden32c
@pytest.mark.exclude
def test_hs2_boyden32c():
    sorter = HerdingSpikes2
    params = dict(
        adjacency_radius=50,
    )
    do_sorting_test(sorter, params, boyden32c_recdir, assert_avg_accuracy=0.1)


@pytest.mark.spikeforest
@pytest.mark.hs2_sqmea64c
@pytest.mark.exclude
def test_hs2_sqmea64c():
    sorter = HerdingSpikes2
    params = dict(
        adjacency_radius=50,
    )
    do_sorting_test(sorter, params, sqmea64c_recdir, assert_avg_accuracy=0.1)


@pytest.mark.spikeforest
@pytest.mark.ks2_neuropix32c
@pytest.mark.exclude
def test_ks2_neuropix32c():
    sorter = KiloSort2
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(sorter, params, neuropix32c_recdir, assert_avg_accuracy=0.5)

@pytest.mark.spikeforest
@pytest.mark.ks2_boyden32c
@pytest.mark.exclude
def test_ks2_boydenc():
    sorter = KiloSort2
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(sorter, params, boyden32c_recdir, assert_avg_accuracy=0.5)


@pytest.mark.spikeforest
@pytest.mark.irc_neuropix32c
@pytest.mark.exclude
def test_irc_neuropix32c():
    sorter = IronClust
    params = dict(
        detect_sign=-1,
        adjacency_radius=50,
    )
    do_sorting_test(sorter, params, neuropix32c_recdir, assert_avg_accuracy=0.5)


@pytest.mark.spikeforest
@pytest.mark.irc_magland_c8
@pytest.mark.exclude
def test_irc_magland_c8():
    sorter = IronClust
    params = dict(
        detect_sign=-1,
        adjacency_radius=75,
    )
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.5)


@pytest.mark.spikeforest
@pytest.mark.irc_magland_c4
@pytest.mark.exclude
def test_irc_magland_c4():
    sorter = IronClust
    params = dict(
        detect_sign=-1,
        adjacency_radius=75,
    )
    do_sorting_test(sorter, params, synth_magland_c4_recdir, assert_avg_accuracy=0.5)


@pytest.mark.spikeforest
@pytest.mark.irc_sqmea64c
@pytest.mark.exclude
def test_irc_sqmea64c():
    sorter = IronClust
    params = dict(
        detect_sign=-1,
        adjacency_radius=50,
    )
    do_sorting_test(sorter, params, sqmea64c_recdir, assert_avg_accuracy=0.1)


@pytest.mark.spikeforest
@pytest.mark.jrc_magland_c8
@pytest.mark.exclude
def test_jrc_magland_c8():
    sorter = JRClust
    params = dict(
        detect_sign=-1,
        adjacency_radius=75,
    )
    do_sorting_test(sorter, params, synth_magland_c8_recdir, assert_avg_accuracy=0.5)    



@pytest.mark.spikeforest
@pytest.mark.jrc_neuropix32c
@pytest.mark.exclude
def test_jrc_neuropix32c():
    sorter = JRClust
    params = dict(
        detect_sign=-1,
        adjacency_radius=75,
    )
    do_sorting_test(sorter, params, neuropix32c_recdir, assert_avg_accuracy=0.5)   


@pytest.mark.spikeforest
@pytest.mark.ks2_kampff
@pytest.mark.exclude
def test_ks2_kampff():
    sorter = KiloSort2
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(sorter, params, kampff1_recdir, assert_avg_accuracy=0.8)


def do_sorting_test(sorting_processor, params, recording_dir, assert_avg_accuracy, container='default'):
    mt.configDownloadFrom('spikeforest.kbucket')

    recdir = recording_dir
    mt.createSnapshot(path=recdir, download_recursive=True)
    sorting = sorting_processor.execute(
        recording_dir=recdir,
        firings_out={'ext': '.mda'},
        **params,
        _container=container,
        _force_run=True
    )

    comparison = sa.GenSortingComparisonTable.execute(
        firings=sorting.outputs['firings_out'],
        firings_true=recdir + '/firings_true.mda',
        units_true=[],
        json_out={'ext': '.json'},
        html_out={'ext': '.html'},
        _container=None,
        _force_run=True
    )

    X = mt.loadObject(path=comparison.outputs['json_out'])
    accuracies = [float(a['accuracy']) for a in X.values()]
    avg_accuracy = np.mean(accuracies)

    print('Average accuracy: {}'.format(avg_accuracy))

    assert(avg_accuracy >= assert_avg_accuracy)

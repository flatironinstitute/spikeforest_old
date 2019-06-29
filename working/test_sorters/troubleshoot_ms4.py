#!/usr/bin/env python

from spikeforestsorters import MountainSort4, MountainSort4Old
from mountaintools import client as mt
import spikeforest_analysis as sa
import numpy as np
import time

synth_magland_c4_recdir = 'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C4/001_synth'
synth_magland_c8_recdir = 'sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C8/001_synth'
kampff1_recdir = 'sha1dir://c86202ca09f303b6c6d761b94975054c29c85d2b.paired_kampff/kampff1'
neuropix32c_recdir = 'sha1dir://d446c8e74fc4ca3a0dab491fca6c10189b527709.neuropix32c.c14'
boyden32c_recdir = 'sha1dir://b28dbf52748dcb401034d1c353807bcbff20e106.boyden32c.1103_1_1'
sqmea64c_recdir = 'sha1dir://e8de6ac2138bf775f29f8ab214d04aa92e20ca79'
paired_mea64c_recdir = 'sha1dir://7f12606802ade3c7c71eb306490b7840eb8b1fb4.paired_mea64c'
neurocube1c_recdir = 'sha1dir://e6cb8f3bb5228c73208a82d2854552af38ab6b40'
visapy30c_recdir = 'sha1dir://97253adc2581b1acbf9a9fffcbc00247d8088a1d.mea_c30.set1'
# synth_bionet_static1_recdir = 'sha1dir://abc900f5cd62436e7c89d914c9f36dcd7fcca0e7.synth_bionet/bionet_static/static_8x_C_4B'
# synth_bionet_static1_recdir = '/mnt/home/jjun/ceph/recordings/bionet_static_rec1'
# synth_bionet_static1_recdir = '/mnt/home/jjun/ceph/groundtruth/bionet/bionet_static/static_8x_A_4A'
synth_bionet_static1_recdir = '/mnt/home/jjun/ceph/groundtruth/bionet/bionet_static/static_8x_C_4B'


def main():
    ## Realizing container file: sha1://e06fee7f72f6b66d80d899ebc08e7c39e5a2458e/2019-05-06/mountainsort4.simg
    ################ ELAPSED for sorting (sec): 49.12553930282593 45
    ################ ELAPSED for comparison (sec): 2.8740932941436768
    ## Average accuracy: 0.8555102436944109 0.88
    # test_ms4_old_magland_c8()

    ## Realizing container file: sha1://8743ff094a26bdedd16f36209a05333f1f82fbd8/2019-06-26/mountainsort4.simg
    ################ ELAPSED for sorting (sec): 61.25473141670227 59
    ################ ELAPSED for comparison (sec): 2.1177682876586914
    ## Average accuracy: 0.9190230371912449 0.85
    # test_ms4_new_magland_c8()

    test_ms4_new_magland_c8(container=None)


def test_ms4_old_magland_c8():
    sorter = MountainSort4Old
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(
        sorter,
        params,
        synth_magland_c8_recdir,
        container='default',
        force_run=True
    )

def test_ms4_new_magland_c8(container='default'):
    sorter = MountainSort4
    params = dict(
        detect_sign=-1,
        adjacency_radius=50
    )
    do_sorting_test(
        sorter,
        params,
        synth_magland_c8_recdir,
        container=container,
        force_run=True
    )
    

def do_sorting_test(
        sorting_processor,
        params,
        recording_dir,
        container='default',
        force_run=True,
        _keep_temp_files=False
    ):
    mt.configDownloadFrom(['spikeforest.kbucket', 'spikeforest.public'])

    recdir = recording_dir
    mt.createSnapshot(path=recdir, download_recursive=True)
    timer = time.time()
    sorting = sorting_processor.execute(
        recording_dir=recdir,
        firings_out={'ext': '.mda'},
        **params,
        _container=container,
        _force_run=force_run,
        _keep_temp_files=_keep_temp_files
    )
    elapsed = time.time() - timer
    print('################ ELAPSED for sorting (sec): {}'.format(elapsed))

    timer = time.time()
    comparison = sa.GenSortingComparisonTable.execute(
        firings=sorting.outputs['firings_out'],
        firings_true=recdir + '/firings_true.mda',
        units_true=[],
        json_out={'ext': '.json'},
        html_out={'ext': '.html'},
        _container='default',
        _force_run=True
    )
    elapsed = time.time() - timer
    print('################ ELAPSED for comparison (sec): {}'.format(elapsed))

    X = mt.loadObject(path=comparison.outputs['json_out'])
    accuracies = [float(a['accuracy']) for a in X.values()]
    avg_accuracy = np.mean(accuracies)

    print('Average accuracy: {}'.format(avg_accuracy))


if __name__ == "__main__":
    main()

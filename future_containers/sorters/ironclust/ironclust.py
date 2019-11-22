#!/usr/bin/env python

import os
import sys
import argparse
import time
import kachery as ka
import spiketoolkit as st
import spikesorters as ss
import spikeextractors as se
from spikeforest_container_utils import AutoRecordingExtractor
from shellscript import ShellScript
from ironclust_sorter import IronClustSorter

def main():
    parser = argparse.ArgumentParser(description='Run spike sorting using MountainSort4.')
    parser.add_argument('recording_path', help='Path (or kachery-path) to the file or directory defining the sorting')
    parser.add_argument('--output', help='The output directory', required=True)

    args = parser.parse_args()
    recording_path = args.recording_path
    output_dir = args.output

    _mkdir_if_needed(output_dir, require_empty=True)

    ka.set_config(fr='default_readonly')

    recording = AutoRecordingExtractor(dict(path=recording_path), download=True)

    # Sorting
    print('Sorting...')
    # IronClustSorter.set_ironclust_path('/src/ironclust')

    sorter = IronClustSorter(
        recording=recording,
        output_folder='/tmp/tmpdir',
        delete_output_folder = False # will be taken care by _keep_temp_files one step above
    )

    sorter.set_params(
        detect_sign=-1,
        adjacency_radius=50,
        adjacency_radius_out=75,
        detect_threshold=4,
        prm_template_name='',
        freq_min=300,
        freq_max=8000,
        merge_thresh=0.99,
        pc_per_chan=0,
        whiten=False,
        filter_type='bandpass',
        filter_detect_type='none',
        common_ref_type='mean',
        batch_sec_drift=300,
        step_sec_drift=20,
        knn=30,
        min_count=30,
        fGpu=True,
        fft_thresh=8,
        fft_thresh_low=0,
        nSites_whiten=32,
        feature_type='gpca',
        delta_cut=1,
        post_merge_mode=1,
        sort_mode=1
    )     
    timer = sorter.run()
    print('#SF-SORTER-RUNTIME#{:.3f}#'.format(timer))
    sorting = sorter.get_result()

    se.MdaSortingExtractor.write_sorting(sorting=sorting, save_path=output_dir + '/firings.mda')

def _mkdir_if_needed(dirpath, *, require_empty=False):
    if os.path.exists(dirpath):
        if not _is_empty_dir(dirpath):
            raise Exception('Output directory already exists and is not empty: {}'.format(dirpath))
    else:
        os.mkdir(dirpath)

def _is_empty_dir(path):
    if not os.path.exists(path):
        return False
    if not os.path.isdir(path):
        return False
    entities = os.listdir(path)
    if len(entities) > 0:
        return False
    return True

if __name__ == "__main__":
    main()

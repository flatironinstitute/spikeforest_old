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
from kilosort2_sorter import Kilosort2Sorter

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

    sorter = Kilosort2Sorter(
        recording=recording,
        output_folder='/tmp/tmpdir',
        delete_output_folder = False # will be taken care by _keep_temp_files one step above
    )

    sorter.set_params(
        detect_sign=-1,
        detect_threshold=5,
        freq_min=150,
        pc_per_chan=3
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

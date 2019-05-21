#!/usr/bin/env python

import argparse
from mountaintools import client as mt
import os
import json


def main():
    parser = argparse.ArgumentParser(description='Show the publicly downloadable studies of SpikeForest')
    parser.add_argument('--group_names', help='Comma-separated list of recording group names.', required=False, default=None)

    args = parser.parse_args()

    mt.configDownloadFrom(['spikeforest.public'])

    if args.group_names is not None:
        group_names = args.output_ids.split(',')
    else:
        group_names = [
            # 'paired_boyden32c',
            'paired_crcns',
            'paired_mea64c',
            'paired_kampff',
            'synth_bionet',
            'synth_magland',
            'manual_franklab',
            'synth_mearec_neuronexus',
            'synth_mearec_tetrode',
            'synth_visapy'
        ]
    print('Using group names: ', group_names)

    print('******************************** LOADING RECORDING GROUPS...')
    studies = []
    study_sets = []
    recordings = []
    for group_name in group_names:
        print('Loading recording group: {}'.format(group_name))
        output_path = ('key://pairio/spikeforest/spikeforest_recording_group.{}.json').format(group_name)
        obj = mt.loadObject(path=output_path)
        if obj:
            studies = studies + obj['studies']
            study_sets = study_sets + obj.get('study_sets', [])
            recordings = recordings + obj['recordings']
            for rec in recordings:
                if rec.get('public', False):
                    print('{}/{}: {}'.format(rec.get('study', ''), rec.get('name', ''), rec.get('directory', '')))
        else:
            print('WARNING: unable to load object: ' + output_path)

if __name__ == "__main__":
    main()

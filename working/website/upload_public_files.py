#!/usr/bin/env python

import argparse
from mountaintools import client as mt
import os
import json


def main():
    parser = argparse.ArgumentParser(description='Upload public files, e.g., console outputs')
    parser.add_argument('--output_ids', help='Comma-separated list of IDs of the analysis outputs to include.', required=False, default=None)

    args = parser.parse_args()

    mt.configDownloadFrom(['spikeforest.kbucket'])

    if args.output_ids is not None:
        output_ids = args.output_ids.split(',')
    else:
        output_ids = [
            'paired_boyden32c',
            'paired_crcns',
            'paired_mea64c',
            'paired_kampff',
            'paired_monotrode',
            'synth_bionet',
            'synth_magland',
            'synth_monotrode',
            'manual_franklab',
            'synth_mearec_neuronexus',
            'synth_mearec_tetrode',
            'synth_visapy'
        ]
    print('Using output ids: ', output_ids)

    for output_id in output_ids:
        print('Loading output object: {}'.format(output_id))
        output_path = ('key://pairio/spikeforest/spikeforest_analysis_results.{}.json').format(output_id)
        obj = mt.loadObject(path=output_path)
        for ii, sr in enumerate(obj['sorting_results']):
            print('{}: sorting result {} of {}'.format(output_id, ii + 1, len(obj['sorting_results'])))
            if 'console_out' in sr:
                mt.createSnapshot(path=sr['console_out'], upload_to='spikeforest.public1')

if __name__ == "__main__":
    main()

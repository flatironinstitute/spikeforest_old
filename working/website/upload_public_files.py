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
            # 'paired_monotrode',
            # 'synth_monotrode',
            'synth_bionet',
            'synth_magland',
            'manual_franklab',
            'synth_mearec_neuronexus',
            'synth_mearec_tetrode',
            'synth_visapy',
            'hybrid_janelia'
        ]

    print('Using output ids: ', output_ids)

    for output_id in output_ids:
        print('Loading output object: {}'.format(output_id))
        output_path = ('key://pairio/spikeforest/spikeforest_analysis_results.{}.json').format(output_id)
        obj = mt.loadObject(path=output_path)
        paths = [
            sr['console_out']
            for sr in obj['sorting_results'] if 'console_out' in sr
        ]
        print('{}: {} sorting results - {} with console_out'.format(output_id, len(obj['sorting_results']), len(paths)))
        mt.createSnapshots(paths=paths, upload_to='spikeforest.public')

if __name__ == "__main__":
    main()

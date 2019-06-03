#!/usr/bin/env python

import argparse
from mountaintools import client as mt
import os
import frontmatter

help_txt = """
This script saves collections in the following .json files in an output directory

Algorithms.json
Sorters.json
SortingResults.json
StudySets.json
StudyAnalysisResults.json
"""


def main():
    parser = argparse.ArgumentParser(description=help_txt, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--output_dir', help='The output directory for saving the files.')
    parser.add_argument('--download-from', help='The output directory for saving the files.', required=False, default='spikeforest.kbucket')
    parser.add_argument('--key_path', help='Key path to retrieve data from')

    args = parser.parse_args()

    output_dir = args.output_dir

    if os.path.exists(output_dir):
        raise Exception('Output directory already exists: {}'.format(output_dir))

    os.mkdir(output_dir)

    mt.configDownloadFrom(args.download_from)

    print('Loading spike-front results object...')
    obj = mt.loadObject(path=args.key_path)

    StudySets = obj['StudySets']
    SortingResults = obj['SortingResults']
    Sorters = obj['Sorters']
    Algorithms = obj['Algorithms']
    StudyAnalysisResults = obj['StudyAnalysisResults']
    General = obj['General']

    print('Saving {} study sets to {}/StudySets.json'.format(len(StudySets), output_dir))
    mt.saveObject(object=StudySets, dest_path=output_dir + '/StudySets.json')

    print('Saving {} sorting results to {}/SortingResults.json'.format(len(SortingResults), output_dir))
    mt.saveObject(object=SortingResults, dest_path=output_dir + '/SortingResults.json')

    print('Saving {} sorters to {}/Sorters.json'.format(len(Sorters), output_dir))
    mt.saveObject(object=Sorters, dest_path=output_dir + '/Sorters.json')

    print('Saving {} algorithms to {}/Algorithms.json'.format(len(Algorithms), output_dir))
    mt.saveObject(object=Algorithms, dest_path=output_dir + '/Algorithms.json')

    print('Saving {} study analysis results to {}/StudyAnalysisResults.json'.format(len(StudySets), output_dir))
    mt.saveObject(object=StudyAnalysisResults, dest_path=output_dir + '/StudyAnalysisResults.json')

    print('Saving general info to {}/General.json'.format(output_dir))
    mt.saveObject(object=General, dest_path=output_dir + '/General.json')

if __name__ == "__main__":
    main()

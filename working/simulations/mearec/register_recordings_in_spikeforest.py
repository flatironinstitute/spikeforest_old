#!/usr/bin/env python

import os
import sfdata as sf
from mountaintools import client as mt


def main():
    path = 'sha1dir://8516cc54587e0c5ddd0709154e7f609b9b7884b4'
    mt.configDownloadFrom('spikeforest.public')
    X = mt.readDir(path)
    for study_set_name, d in X['dirs'].items():
        study_sets = []
        studies = []
        recordings = []
        study_sets.append(dict(
            name=study_set_name + '_b',
            info=dict(),
            description=''
        ))
        for study_name, d2 in d['dirs'].items():
            study_dir = path + '/' + study_set_name + '/' + study_name
            study0 = dict(
                name=study_name,
                study_set=study_set_name + '_b',
                directory=study_dir,
                description=''
            )
            studies.append(study0)
            index_within_study = 0
            for recording_name, d3 in d2['dirs'].items():
                recdir = study_dir + '/' + recording_name
                recordings.append(dict(
                    name=recording_name,
                    study=study_name,
                    directory=recdir,
                    firings_true=recdir + '/firings_true.mda',
                    index_within_study=index_within_study,
                    description='One of the recordings in the {} study'.format(study_name)
                ))
                index_within_study = index_within_study + 1

        print('Saving object...')
        group_name = study_set_name + '_b'
        address = mt.saveObject(
            object=dict(
                studies=studies,
                recordings=recordings,
                study_sets=study_sets
            ),
            key=dict(name='spikeforest_recording_group', group_name=group_name),
            upload_to='spikeforest.public'
        )
        if not address:
            raise Exception('Problem uploading object to {}'.format(ut))

        output_fname = 'key://pairio/spikeforest/spikeforest_recording_group.{}.json'.format(group_name)
        print('Saving output to {}'.format(output_fname))
        mt.createSnapshot(path=address, dest_path=output_fname)

if __name__ == "__main__":
    main()


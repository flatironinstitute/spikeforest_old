#!/usr/bin/env python

from mountaintools import client as mt
import os

mt.login()
upload_to = 'kbucket'


# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'

group_name = 'magland_synth'

def prepare_magland_synth_studies(*, basedir):
    study_set_name = 'magland_synth'
    study_set_dir0 = basedir+'/magland_synth'
    study_set_dir = mt.createSnapshot(study_set_dir0, upload_to=upload_to, upload_recursive=False, download_recursive=False)
    studies = []
    recordings = []
    names = []
    names = names+['datasets_noise10_K10_C4', 'datasets_noise10_K10_C8']
    names = names+['datasets_noise10_K20_C4', 'datasets_noise10_K20_C8']
    names = names+['datasets_noise20_K10_C4', 'datasets_noise20_K10_C8']
    names = names+['datasets_noise20_K20_C4', 'datasets_noise20_K20_C8']
    description = mt.loadText(path=study_set_dir+'/readme.txt')
    for name in names:
        print('PREPARING: '+name)
        study_name = 'magland_synth_'+name[9:]
        study_dir = study_set_dir+'/'+name
        study0 = dict(
            name=study_name,
            study_set=study_set_name,
            directory=study_dir,
            description=description
        )
        studies.append(study0)
        dd = mt.readDir(study_dir)
        for dsname in dd['dirs']:
            dsdir = '{}/{}'.format(study_dir, dsname)
            recordings.append(dict(
                name=dsname,
                study=study_name,
                directory=dsdir,
                firings_true=dsdir+'/firings_true.mda',
                description='One of the recordings in the {} study'.format(
                    study_name)
            ))
    return studies, recordings


# Prepare the studies
studies, recordings = prepare_magland_synth_studies(basedir=basedir)
print('Saving object...')
address = mt.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings
    ),
    key=dict(name='spikeforest_recording_group', group_name=group_name),
    upload_to=upload_to
)
if not address:
    raise Exception('Problem saving object.')

output_fname = 'key://pairio/spikeforest/spikeforest_recording_group.{}.json'.format(group_name)
print('Saving output to {}'.format(output_fname))
mt.createSnapshot(path=address, dest_path=output_fname)

print('Done.')

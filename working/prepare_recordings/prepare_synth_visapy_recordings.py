#!/usr/bin/env python

import os
from mountaintools import client as mt
from load_study_set_from_md import load_study_set_from_md

# mt.login()
upload_to = 'spikeforest.kbucket'
upload_public_to = 'spikeforest.public'

# The base directory used below
# basedir = 'kbucket://15734439d8cf/groundtruth'
basedir = os.getenv('GROUNDTRUTH_PATH', '/mnt/home/jjun/ceph/groundtruth')

group_name = 'synth_visapy'


def prepare_synth_visapy_studies(*, basedir):
    study_sets = [
        load_study_set_from_md('descriptions/spf_synth_visapy.md')
    ]
    study_set_name = study_sets[0]['name']

    study_set_dir0 = basedir + '/visapy_synth'
    study_set_dir = mt.createSnapshot(study_set_dir0, upload_to=upload_to, upload_recursive=False, download_recursive=False)
    if not study_set_dir:
        raise Exception('Failed to create snapshot of study set directory: ' + study_set_dir0)
    study_set_dir = study_set_dir + '.synth_visapy'
    print('Using study set dir: ' + study_set_dir)
    studies = []
    recordings = []
    study_names = ['mea_c30']
    for study_name in study_names:
        print('PREPARING: ' + study_name)
        study_dir = study_set_dir + '/' + study_name
        study0 = dict(
            name=study_name,
            study_set=study_set_name,
            directory=study_dir,
            description=''
        )
        studies.append(study0)
        dd = mt.readDir(study_dir)
        for dsname in dd['dirs']:
            dsdir = '{}/{}'.format(study_dir, dsname)
            recordings.append(dict(
                name=dsname,
                study=study_name,
                directory=dsdir,
                firings_true=dsdir + '/firings_true.mda',
                description='One of the recordings in the {} study'.format(
                    study_name)
            ))
    return studies, recordings, study_sets


# Prepare the studies
studies, recordings, study_sets = prepare_synth_visapy_studies(basedir=basedir)

print('Uploading files to kachery...')
for rec in recordings:
    mt.createSnapshot(rec['directory'], upload_to=upload_to, upload_recursive=True)
    if rec['index_within_study'] == 0:
        mt.createSnapshot(rec['directory'], upload_to=upload_public_to, upload_recursive=True)
        rec['public'] = True

print('Saving object...')
address = mt.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings,
        study_sets=study_sets
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

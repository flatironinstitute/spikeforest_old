#!/usr/bin/env python

from mountaintools import client as mt
import os
import frontmatter
from load_study_set_from_md import load_study_set_from_md

# mt.login()
upload_to = 'spikeforest.kbucket'
upload_public_to = 'spikeforest.public1'

# The base directory used below
# basedir = 'kbucket://15734439d8cf/groundtruth'
basedir = os.getenv('GROUNDTRUTH_PATH', '/mnt/home/jjun/ceph/groundtruth')

group_name = 'test_reliability'


def prepare_test_reliability_studies(*, basedir):
    study_sets = [
        load_study_set_from_md('descriptions/spf_test_reliability.md')
    ]
    study_set_name = study_sets[0]['name']

    study_set_dir0 = basedir + '/test_reliability'
    print('Creating snapshot of study set directory...')
    study_set_dir = mt.createSnapshot(study_set_dir0, upload_to=upload_to, upload_recursive=False, download_recursive=False)
    if not study_set_dir:
        raise Exception('Failed to create snapshot of study set directory: ' + study_set_dir0)
    # study_set_dir = study_set_dir + '.test_reliability'
    print('Using study set dir: ' + study_set_dir)
    studies = []
    recordings = []
    names = ['001_synth','002_synth','003_synth','004_synth','005_synth','006_synth','007_synth','008_synth','009_synth','010_synth']
    # description = mt.loadText(path=study_set_dir + '/readme.txt')
    for name in names:
        print('PREPARING: ' + name)
        study_name = 'test_reliability_' + name
        study_dir = study_set_dir + '/' + name
        study0 = dict(
            name=study_name,
            study_set=study_set_name,
            directory=study_dir,
            description=''
        )
        studies.append(study0)
        dd = mt.readDir(study_dir)
        for i, dsname in enumerate(dd['dirs']):
            dsdir = '{}/{}'.format(study_dir, dsname)
            recordings.append(dict(
                name=dsname,
                study=study_name,
                directory=dsdir,
                firings_true=dsdir + '/firings_true.mda',
                index_within_study=i,
                description='One of the recordings in the {} study'.format(
                    study_name)
            ))
    return studies, recordings, study_sets


# Prepare the studies
studies, recordings, study_sets = prepare_test_reliability_studies(basedir=basedir)

print('Uploading files to kachery...')
for rec in recordings:
    mt.createSnapshot(rec['directory'], upload_to=upload_to, upload_recursive=True)
    if rec['index_within_study'] == 0:
        mt.createSnapshot(rec['directory'], upload_to=upload_public_to, upload_recursive=True)
        rec['public'] = True

print('Saving object...')
for ut in [upload_to, upload_public_to]:
    address = mt.saveObject(
        object=dict(
            studies=studies,
            recordings=recordings,
            study_sets=study_sets
        ),
        key=dict(name='spikeforest_recording_group', group_name=group_name),
        upload_to=ut
    )
    if not address:
        raise Exception('Problem uploading object to {}'.format(ut))

output_fname = 'key://pairio/spikeforest/spikeforest_recording_group.{}.json'.format(group_name)
print('Saving output to {}'.format(output_fname))
mt.createSnapshot(path=address, dest_path=output_fname)

print('Done.')

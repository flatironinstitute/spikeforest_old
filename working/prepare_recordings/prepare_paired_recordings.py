#!/usr/bin/env python
from mountaintools import client as mt
from load_study_set_from_md import load_study_set_from_md

# mt.login()
upload_to = 'spikeforest.kbucket'

# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'

# HIGH TODO separate out the paired recordings into different study sets
# HIGH TODO load study set descriptions for website

def prepare_paired_studies(*, basedir, name):
    study_sets = [
        load_study_set_from_md('descriptions/spf_paired_'+name)
    ]
    study_set_name = study_sets[0]['name']

    study_dir0 = basedir+'/paired_recordings/'+name
    study_dir = mt.createSnapshot(study_dir0, upload_to=upload_to, upload_recursive=False, download_recursive=False)
    if not study_dir:
        raise Exception('Failed to create snapshot of directory: '+study_dir0)
    study_dir=study_dir+'.paired_'+name

    studies = []
    recordings = []
    study_set_dir = study_dir
    print('Using study set dir: '+study_set_dir)

    print('PREPARING: '+name)
    study_name = 'paired_' + name
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
            firings_true=dsdir+'/firings_true.mda',
            description='One of the recordings in the {} study'.format(
                study_name)
        ))
    return studies, recordings, study_sets


# Prepare the studies
names = ['boyden32c','crcns','mea64c','neuropix32c']
study_sets = []
for name in names:
    group_name = 'paired_'+name
    print('PREPARING {}'.format(name))
    studies, recordings, study_sets = prepare_paired_studies(basedir=basedir, name=name)
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

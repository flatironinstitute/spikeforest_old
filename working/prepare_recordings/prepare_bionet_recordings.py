import sfdata as sf
from mountaintools import client as mt

mt.login()
upload_to = 'spikeforest.spikeforest2'

# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'

group_name = 'bionet'


def prepare_bionet_studies(*, basedir):
    study_set_name = 'bionet'
    studies = []
    recordings = []
    names = ['static', 'drift', 'shuffle']
    for name in names:
        study_name = 'bionet_' + name
        print('PREPARING: '+study_name)
        study_dir = basedir+'/bionet/' + study_name
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
                description='One of the recordings in the {} study'.format(
                    study_name)
            ))
    return studies, recordings


# Prepare the studies
studies, recordings = prepare_bionet_studies(basedir=basedir)
mt.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings
    ),
    key=dict(name='spikeforest_recording_group', group_name=group_name),
    upload_to=upload_to
)

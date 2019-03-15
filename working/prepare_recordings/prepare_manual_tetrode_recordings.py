import sfdata as sf
from mountaintools import client as mt

mt.login()
mt.configRemoteReadWrite(collection='spikeforest', share_id='spikeforest.spikeforest2')

# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'

group_name = 'manual_tetrode'


def prepare_manual_tetrode_studies(*, basedir):
    study_set_name = 'manual_tetrode'
    studies = []
    recordings = []
    names = ['600s', '1200s', '2400s']
    for name in names:
        study_name = 'manual_tetrode_' + name
        print('PREPARING: '+study_name)
        study_dir = basedir+'/manual_sortings/tetrode_'+name
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
studies, recordings = prepare_manual_tetrode_studies(basedir=basedir)
mt.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings
    ),
    key=dict(name='spikeforest_recording_group', group_name=group_name)
)

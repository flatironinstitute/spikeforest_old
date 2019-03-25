import sfdata as sf
from mountaintools import client as mt

mt.login()
mt.configRemoteReadWrite(collection='spikeforest', share_id='spikeforest.spikeforest2')

# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'

group_name = 'hybrid_drift'


def prepare_hybrid_drift_studies(*, basedir):
    study_set_name = 'hybrid_drift'
    studies = []
    recordings = []
    names = ['16c_600s', '16c_1200s', '32c_600s', '32c_1200s', '64c_600s', '64c_1200s']
    for name in names:
        study_name = 'hybrid_drift_' + name
        print('PREPARING: '+study_name)
        study_dir = basedir+'/hybrid_drift'
        study0 = dict(
            name=study_name,
            study_set=study_set_name,
            directory=study_dir,
            description=''
        )
        studies.append(study0)
        dd = mt.readDir(study_dir)
        for dsname in dd['dirs']:
            if name in dsname:
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
studies, recordings = prepare_hybrid_drift_studies(basedir=basedir)
mt.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings
    ),
    key=dict(name='spikeforest_recording_group', group_name=group_name)
)

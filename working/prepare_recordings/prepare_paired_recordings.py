import sfdata as sf
from mountaintools import client as mt

mt.login()
mt.configRemoteReadWrite(collection='spikeforest', share_id='spikeforest.spikeforest2')

# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'

group_name = 'paired'


def prepare_paired_studies(*, basedir):
    study_set_name = 'paired'
    studies = []
    recordings = []
    #names = ['boyden32c','crcns','mea64c','neuronexus32c','neuropix32c']
    names = ['boyden32c','crcns','mea64c','neuropix32c'] # exclude neuro
    for name in names:
        print('PREPARING: '+name)
        study_name = 'paired_' + name
        study_dir = basedir+'/paired_recordings/'+name
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
studies, recordings = prepare_paired_studies(basedir=basedir)
mt.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings
    ),
    key=dict(name='spikeforest_recording_group', group_name=group_name)
)

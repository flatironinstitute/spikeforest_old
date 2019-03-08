#%%
# import sfdata as sf
from mountaintools import client as mt

mt.login()
mt.configRemoteReadWrite(collection='spikeforest', share_id='spikeforest.spikeforest2')

# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'

group_name = 'mearec_neuronexus'

#%%
def prepare_mearec_neuronexus_studies(*, basedir):
    study_set_name = 'mearec_neuronexus'
    studies = []
    recordings = []
    names = []
    names=names+['datasets_noise10_K10_C32','datasets_noise10_K20_C32','datasets_noise10_K40_C32']
    names=names+['datasets_noise20_K10_C32','datasets_noise20_K20_C32','datasets_noise20_K40_C32']
    for name in names:
        print('PREPARING: '+name)
        study_name = 'mearec_neuronexus'
        study_dir = basedir+'/mearec_synth/neuronexus'
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

#%%
# Prepare the studies
studies, recordings = prepare_mearec_neuronexus_studies(basedir=basedir)

#%%
mt.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings
    ),
    key=dict(name='spikeforest_recording_group', group_name=group_name)
)


#%%

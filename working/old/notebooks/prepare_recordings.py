# %% Change working directory from the workspace root to the ipynb file location. Turn this addition off with the DataScience.changeDirOnImportExport setting
from mountaintools import client as ca
import sfdata as sf
import os
try:
    os.chdir(os.path.join(os.getcwd(), 'working/notebooks'))
    print(os.getcwd())
except:
    pass

# %%
get_ipython().run_line_magic('load_ext', 'autoreload')
get_ipython().run_line_magic('autoreload', '2')


password = os.environ.get('SPIKEFOREST_PASSWORD')
ca.autoConfig(collection='spikeforest', key='spikeforest2-readwrite',
              ask_password=True, password=password)


# %%
ca.loadObject(key=dict(name='spikeforest_recording_group_names'))


# %%
# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'


# %%
ca.saveObject(
    key=dict(name='spikeforest_recording_group_names'),
    object=[
        'magland_synth',
        'magland_synth_test',
        'mearec_sqmea_test',
    ]
)

# %% [markdown]
# # MAGLAND SYNTH

# %%


def prepare_magland_synth_studies(*, basedir):
    study_set_name = 'magland_synth'
    studies = []
    recordings = []
    names = []
    names = names+['datasets_noise10_K10_C4', 'datasets_noise10_K10_C8']
    names = names+['datasets_noise10_K20_C4', 'datasets_noise10_K20_C8']
    names = names+['datasets_noise20_K10_C4', 'datasets_noise20_K10_C8']
    names = names+['datasets_noise20_K20_C4', 'datasets_noise20_K20_C8']
    description = ca.loadText(path=basedir+'/magland_synth/readme.txt')
    for name in names:
        study_name = 'magland_synth_'+name[9:]
        study_dir = basedir+'/magland_synth/'+name
        study0 = dict(
            name=study_name,
            study_set=study_set_name,
            directory=study_dir,
            description=description
        )
        studies.append(study0)
        dd = ca.readDir(study_dir)
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


# %%
# Prepare the studies
studies, recordings = prepare_magland_synth_studies(basedir=basedir)
ca.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings
    ),
    key=dict(name='spikeforest_recording_group', group_name='magland_synth')
)
ca.saveObject(
    object=dict(
        studies=[studies[0]],
        recordings=recordings[0:3]
    ),
    key=dict(name='spikeforest_recording_group',
             group_name='magland_synth_test')
)


# %%
# Summarize the recordings


# %% SQ_MEAREC
def prepare_mearec_sqmea_studies(*, basedir):
    study_set_name = 'mearec_sqmea'
    studies = []
    recordings = []
    names = []
    names = names+['datasets_noise10_K100_C100']

    description = ca.loadText(path=basedir+'/mearec_synth/sqmea/readme.md')
    for name in names:
        study_name = 'mearec_sqmea_'+name[9:]
        study_dir = basedir+'/mearec_synth/sqmea/'+name
        study0 = dict(
            name=study_name,
            study_set=study_set_name,
            directory=study_dir,
            description=description
        )
        studies.append(study0)
        dd = ca.readDir(study_dir)
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


# %%
studies, recordings = prepare_mearec_sqmea_studies(basedir=basedir)

ca.saveObject(
    object=dict(
        studies=[studies[0]],
        recordings=recordings[0:3]
    ),
    key=dict(name='spikeforest_recording_group',
             group_name='mearec_sqmea_test')
)


# %%

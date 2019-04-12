import sfdata as sf
from mountaintools import client as mt

mt.login()
mt.configRemoteReadWrite(collection='spikeforest', share_id='spikeforest.spikeforest2')

# The base directory used below
basedir = 'kbucket://15734439d8cf/groundtruth'

group_name = 'visapy_mea'

def prepare_visapy_mea_studies(*, basedir):
    study_set_name = 'visapy_mea'
    study_dir0 = basedir+'/visapy_mea'
    study_dir = mt.createSnapshot(study_dir0, upload_to='spikeforest.spikeforest2', upload_recursive=False, download_recursive=False)
    if not study_dir:
        raise Exception('Failed to create snapshot of directory: '+study_dir0)
    study_dir=study_dir+'.visapy_mea'
    print('Using study dir: '+study_dir)
    studies = []
    recordings = []
    names = []
    names = names+['visapy_mea']
    for name in names:
        print('PREPARING: '+name)
        study_name = 'visapy_mea'
        study_dir = study_dir
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
    return studies, recordings


# Prepare the studies
studies, recordings = prepare_visapy_mea_studies(basedir=basedir)
print('Saving object...')
address = mt.saveObject(
    object=dict(
        studies=studies,
        recordings=recordings
    ),
    key=dict(name='spikeforest_recording_group', group_name=group_name)
)
if not address:
    raise Exception('Problem saving object.')

output_fname = 'key://pairio/spikeforest/spikeforest_recording_group.{}.json'.format(group_name)
print('Saving output to {}'.format(output_fname))
mt.createSnapshot(path=address, dest_path=output_fname)

print('Done.')

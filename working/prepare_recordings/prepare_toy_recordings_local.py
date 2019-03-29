from spikeforest import example_datasets
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
import os
import shutil
from mountaintools import client as mt

def prepare_toy_recordings():
    studies = []
    recordings = []
    studies.append(dict(
        name='toy_study',
        study_set='toy_recordings',
        directory='',
        description='toy recordings for local testing'
    ))
    recordings = recordings + _generate_toy_recordings()
    return studies, recordings


def main():
    # Prepare the study and recordings
    print('Preparing toy recordings...')
    studies, recordings = prepare_toy_recordings()

    print('Saving recording group locally...')
    mt.saveObject(
        object=dict(
            studies=studies,
            recordings=recordings
        ),
        #key=dict(name='spikeforest_recording_group', group_name='toy_recordings')
        key=dict(name='spikeforest_recording_groups'),
        subkey='toy_recordings'
    )


def _generate_toy_recordings():
    # generate toy recordings
    if not os.path.exists('toy_recordings'):
        os.mkdir('toy_recordings')

    replace_recordings = False

    ret = []
    for K in [5, 10, 15, 20]:
        recpath = 'toy_recordings/example_K{}'.format(K)
        if os.path.exists(recpath) and (replace_recordings):
            print('Generating toy recording: {}'.format(recpath))
            shutil.rmtree(recpath)
        else:
            print('Recording already exists: {}'.format(recpath))
        if not os.path.exists(recpath):
            rx, sx_true = example_datasets.toy_example1(
                duration=60, num_channels=4, samplerate=30000, K=K)
            SFMdaRecordingExtractor.writeRecording(
                recording=rx, save_path=recpath)
            SFMdaSortingExtractor.writeSorting(
                sorting=sx_true, save_path=recpath+'/firings_true.mda')
        ret.append(dict(
            name='example_K{}'.format(K),
            study='toy_study',
            directory=os.path.abspath(recpath),
            description='A toy recording with K={} units'.format(K)            
        ))

    return ret

if __name__ == '__main__':
    main()
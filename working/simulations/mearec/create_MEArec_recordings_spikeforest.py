#!/usr/bin/env python

import MEArec as mr
from pprint import pprint
from pathlib import Path
from copy import deepcopy
import shutil
import os
import numpy as np
import mlprocessors as mlpr
import multiprocessing
from mountaintools import client as mt
import mtlogging
import random
import spikeextractors as se


@mtlogging.log(root=True)
def main():
    mt.configDownloadFrom('spikeforest.public')
    templates_path = 'sha1dir://95dba567b5168bacb480411ca334ffceb96b8c19.2019-06-11.templates'
    recordings_path = 'recordings_out'

    tempgen_tetrode = templates_path + '/templates_tetrode.h5'
    tempgen_neuronexus = templates_path + '/templates_neuronexus.h5'
    tempgen_neuropixels = templates_path + '/templates_neuropixels.h5'
    tempgen_neuronexus_drift = templates_path + '/templates_neuronexus_drift.h5'

    noise_level = [10, 20]
    duration = 600
    bursting = [False, True]
    nrec = 2  # change this to 10
    ei_ratio = 0.8
    rec_dict = {
        'tetrode': {
            'ncells': [10, 20], 'tempgen': tempgen_tetrode, 'drifting': False
        },
        'neuronexus': {
            'ncells': [10, 20, 40], 'tempgen': tempgen_neuronexus, 'drifting': False
        },
        'neuropixels': {
            'ncells': [20, 40, 60], 'tempgen': tempgen_neuropixels, 'drifting': False
        },
        #'neuronexus_drift': {
        #    'ncells': [10, 20, 40], 'tempgen': tempgen_neuronexus_drift, 'drifting': True
        #}
    }

    # optional: if drifting change drift velocity
    # recording_params['recordings']['drift_velocity] = ...

    # Generate and save recordings
    if os.path.exists(recordings_path):
        shutil.rmtree(recordings_path)
    os.mkdir(recordings_path)

    # Set up slurm configuration
    slurm_working_dir = 'tmp_slurm_job_handler_' + _random_string(5)
    job_handler = mlpr.SlurmJobHandler(
        working_dir=slurm_working_dir
    )
    use_slurm=True
    job_timeout = 3600 * 4
    if use_slurm:
        job_handler.addBatchType(
            name='default',
            num_workers_per_batch=4,
            num_cores_per_job=6,
            time_limit_per_batch=job_timeout * 3,
            use_slurm=True,
            max_simultaneous_batches=20,
            additional_srun_opts=['-p ccm']
        )
    else:
        job_handler.addBatchType(
            name='default',
            num_workers_per_batch=multiprocessing.cpu_count(),
            num_cores_per_job=2,
            max_simultaneous_batches=1,
            use_slurm=False
        )
    with mlpr.JobQueue(job_handler=job_handler) as JQ:
        results_to_write = []
        for rec_type in rec_dict.keys():
            study_set_name = 'synth_mearec_{}'.format(rec_type)
            os.mkdir(recordings_path + '/' + study_set_name)
            params = dict()
            params['duration'] = duration
            params['drifting'] = rec_dict[rec_type]['drifting']
            # reduce minimum distance for dense recordings
            params['min_dist'] = 15
            for ncells in rec_dict[rec_type]['ncells']:
                # changing number of cells
                n_exc = int(ei_ratio * 10)   # intentionally replaced nrec by 10 here
                params['n_exc'] = n_exc
                params['n_inh'] = ncells - n_exc
                for n in noise_level:
                    # changing noise level
                    params['noise_level'] = n
                    for b in bursting:
                        bursting_str = ''
                        if b:
                            bursting_str = '_bursting'
                        study_name = 'synth_mearec_{}_noise{}_K{}{}'.format(rec_type, n, ncells, bursting_str)
                        os.mkdir(recordings_path + '/' + study_set_name + '/' + study_name)
                        for i in range(nrec):
                            # set random seeds
                            params['seed'] = i  # intentionally doing it this way

                            # changing bursting and shape modulation
                            print('Generating', rec_type, 'recording with', ncells, 'noise level', n, 'bursting', b)
                            params['bursting'] = b
                            params['shape_mod'] = b
                            templates0 = mt.realizeFile(path=rec_dict[rec_type]['tempgen'])
                            result0 = GenerateMearecRecording.execute(**params, templates_in=templates0, recording_out=dict(ext='.h5'))
                            mda_output_folder = recordings_path + '/' + study_set_name + '/' + study_name + '/' + '{}'.format(i)
                            results_to_write.append(dict(
                                result=result0,
                                mda_output_folder=mda_output_folder
                            ))
        JQ.wait()

        for x in results_to_write:
            result0: mlpr.MountainJobResult = x['result']
            mda_output_folder = x['mda_output_folder']
            path = mt.realizeFile(path=result0.outputs['recording_out'])
            recording = se.MEArecRecordingExtractor(recording_path=path)
            sorting_true = se.MEArecSortingExtractor(recording_path=path)
            se.MdaRecordingExtractor.write_recording(recording=recording, save_path=mda_output_folder)
            se.MdaSortingExtractor.write_sorting(sorting=sorting_true, save_path=mda_output_folder + '/firings_true.mda')
            if result0.console_out:
                mt.realizeFile(path=result0.console_out, dest_path=mda_output_folder + '.console_out.txt')
            if result0.runtime_info:
                mt.saveObject(object=result0.runtime_info, dest_path=mda_output_folder + '.runtime_info.json')

    print('Creating and uploading snapshot...')
    sha1dir_path = mt.createSnapshot(path=recordings_path, upload_to='spikeforest.public', upload_recursive=True)
    sha1dir_path = mt.createSnapshot(path=recordings_path, upload_to='spikeforest.kbucket', upload_recursive=False)
    print(sha1dir_path)

class GenerateMearecRecording(mlpr.Processor):
    NAME = "GenerateMearecRecording"
    VERSION = "0.1.0"

    # input file
    templates_in = mlpr.Input(description='.h5 file containing templates')

    # output file
    recording_out = mlpr.Output()

    # recordings params
    drifting = mlpr.BoolParameter()
    noise_level = mlpr.FloatParameter()
    bursting = mlpr.BoolParameter()
    shape_mod = mlpr.BoolParameter()

    # spiketrains params
    duration = mlpr.FloatParameter()
    n_exc = mlpr.IntegerParameter()
    n_inh = mlpr.IntegerParameter()

    # templates params
    min_dist = mlpr.FloatParameter()

    # seed
    seed = mlpr.IntegerParameter()

    def run(self):
        recordings_params = deepcopy(mr.get_default_recordings_params())

        recordings_params['recordings']['drifting'] = self.drifting
        recordings_params['recordings']['noise_level'] = self.noise_level
        recordings_params['recordings']['bursting'] = self.bursting
        recordings_params['recordings']['shape_mod'] = self.shape_mod
        recordings_params['recordings']['seed'] = self.seed
        # recordings_params['recordings']['chunk_conv_duration'] = 0  # turn off parallel execution

        recordings_params['spiketrains']['duration'] = self.duration
        recordings_params['spiketrains']['n_exc'] = self.n_exc
        recordings_params['spiketrains']['n_inh'] = self.n_inh
        recordings_params['spiketrains']['seed'] = self.seed

        recordings_params['templates']['min_dist'] = self.min_dist
        recordings_params['templates']['seed'] = self.seed

        # this is needed because mr.load_templates requires the file extension
        templates_fname = self.templates_in + '.h5'
        shutil.copyfile(self.templates_in, templates_fname)
        tempgen = mr.load_templates(Path(templates_fname))

        recgen = mr.gen_recordings(params=recordings_params, tempgen=tempgen, verbose=False)
        mr.save_recording_generator(recgen, self.recording_out)
        del recgen

def _random_string(num_chars):
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return ''.join(random.choice(chars) for _ in range(num_chars))

if __name__ == "__main__":
    main()

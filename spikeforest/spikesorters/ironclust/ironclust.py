import mlprocessors as mlpr
import spikeforest.spikeextractors as se

import os
import time
import numpy as np
from os.path import join
from subprocess import Popen, PIPE
import shlex
import random
import string
import shutil
from spikeforest.spikeextractors import mdaio
import spikeforest.spikeextractors as se
from cairio import client as ca
import json


class IronClust(mlpr.Processor):
    NAME = 'IronClust'
    VERSION = '0.2.0'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    ADDITIONAL_FILES = ['*.m']
    CONTAINER = None
    CONTAINER_SHARE_ID = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(
        'Use -1, 0, or 1, depending on the sign of the spikes in the recording')
    adjacency_radius = mlpr.FloatParameter(
        'Use -1 to include all channels in every neighborhood')
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=5, description='detection threshold')
    prm_template_name = mlpr.StringParameter(
        optional=True, description='.prm template file name')
    freq_min = mlpr.FloatParameter(
        optional=True, default=300, description='Use 0 for no bandpass filtering')
    freq_max = mlpr.FloatParameter(
        optional=True, default=6000, description='Use 0 for no bandpass filtering')
    merge_thresh = mlpr.FloatParameter(
        optional=True, default=0.98, description='TODO')
    pc_per_chan = mlpr.IntegerParameter(
        optional=True, default=3, description='TODO')

    def run(self):
        ironclust_path = os.environ.get('IRONCLUST_PATH', None)
        if not ironclust_path:
            raise Exception('Environment variable not set: IRONCLUST_PATH')

        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp')+'/ironclust-tmp-'+code

        try:
            recording = se.MdaRecordingExtractor(self.recording_dir)
            params = read_dataset_params(self.recording_dir)
            if len(self.channels) > 0:
                recording = se.SubRecordingExtractor(
                    parent_recording=recording, channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
            sorting = ironclust_helper(
                recording=recording,
                tmpdir=tmpdir,
                detect_sign=self.detect_sign,
                adjacency_radius=self.adjacency_radius,
                detect_threshold=self.detect_threshold,
                merge_thresh=self.merge_thresh,
                freq_min=self.freq_min,
                freq_max=self.freq_max,
                pc_per_chan=self.pc_per_chan,
                prm_template_name=self.prm_template_name,
                ironclust_path=ironclust_path,
                params=params,
            )
            se.MdaSortingExtractor.writeSorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                if not getattr(self, '_keep_temp_files', False):
                    shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            shutil.rmtree(tmpdir)


def ironclust_helper(*,
                     recording,  # Recording object
                     tmpdir,  # Temporary working directory
                     detect_sign=-1,  # Polarity of the spikes, -1, 0, or 1
                     adjacency_radius=-1,  # Channel neighborhood adjacency radius corresponding to geom file
                     detect_threshold=5,  # Threshold for detection
                     merge_thresh=.98,  # Cluster merging threhold 0..1
                     freq_min=300,  # Lower frequency limit for band-pass filter
                     freq_max=6000,  # Upper frequency limit for band-pass filter
                     pc_per_chan=3,  # Number of pc per channel
                     prm_template_name='',  # Name of the template file
                     ironclust_path=None,
                     params=dict()
                     ):
    if ironclust_path is None:
        ironclust_path = os.getenv('ironclust_path', None)
    if not ironclust_path:
        raise Exception(
            'You must either set the ironclust_path environment variable, or pass the ironclust_path parameter')
    # source_dir=os.path.dirname(os.path.realpath(__file__))

    dataset_dir = tmpdir+'/ironclust_dataset'
    # Generate three files in the dataset directory: raw.mda, geom.csv, params.json
    se.MdaRecordingExtractor.writeRecording(
        recording=recording, save_path=dataset_dir, params=params)

    samplerate = recording.getSamplingFrequency()

    print('Reading timeseries header...')
    HH = mdaio.readmda_header(dataset_dir+'/raw.mda')
    num_channels = HH.dims[0]
    num_timepoints = HH.dims[1]
    duration_minutes = num_timepoints/samplerate/60
    print('Num. channels = {}, Num. timepoints = {}, duration = {} minutes'.format(
        num_channels, num_timepoints, duration_minutes))

    print('Creating argfile.txt...')
    txt = ''
    txt += 'samplerate={}\n'.format(samplerate)
    txt += 'detect_sign={}\n'.format(detect_sign)
    txt += 'adjacency_radius={}\n'.format(adjacency_radius)
    txt += 'detect_threshold={}\n'.format(detect_threshold)
    txt += 'merge_thresh={}\n'.format(merge_thresh)
    txt += 'freq_min={}\n'.format(freq_min)
    txt += 'freq_max={}\n'.format(freq_max)
    txt += 'pc_per_chan={}\n'.format(pc_per_chan)
    txt += 'prm_template_name={}\n'.format(prm_template_name)
    if 'scale_factor' in params:
        txt += 'scale_factor={}\n'.format(params["scale_factor"])
    _write_text_file(dataset_dir+'/argfile.txt', txt)

    print('Running IronClust...')
    cmd_path = "addpath('{}', '{}/matlab', '{}/matlab/mdaio');".format(
        ironclust_path, ironclust_path, ironclust_path)
    # "p_ironclust('$(tempdir)','$timeseries$','$geom$','$prm$','$firings_true$','$firings_out$','$(argfile)');"
    cmd_call = "p_ironclust('{}', '{}', '{}', '', '', '{}', '{}');"\
        .format(tmpdir, dataset_dir+'/raw.mda', dataset_dir+'/geom.csv', tmpdir+'/firings.mda', dataset_dir+'/argfile.txt')
    cmd = 'matlab -nosplash -nodisplay -r "{} {} quit;"'.format(
        cmd_path, cmd_call)
    print(cmd)
    retcode = _run_command_and_print_output(cmd)

    if retcode != 0:
        raise Exception('IronClust returned a non-zero exit code')

    # parse output
    result_fname = tmpdir+'/firings.mda'
    if not os.path.exists(result_fname):
        raise Exception('Result file does not exist: ' + result_fname)

    firings = mdaio.readmda(result_fname)
    sorting = se.NumpySortingExtractor()
    sorting.setTimesLabels(firings[1, :], firings[2, :])
    return sorting


def _read_text_file(fname):
    with open(fname) as f:
        return f.read()


def _write_text_file(fname, str):
    with open(fname, 'w') as f:
        f.write(str)


def _run_command_and_print_output(command):
    with Popen(shlex.split(command), stdout=PIPE, stderr=PIPE) as process:
        while True:
            output_stdout = process.stdout.readline()
            output_stderr = process.stderr.readline()
            if (not output_stdout) and (not output_stderr) and (process.poll() is not None):
                break
            if output_stdout:
                print(output_stdout.decode())
            if output_stderr:
                print(output_stderr.decode())
        rc = process.poll()
        return rc


def read_dataset_params(dsdir):
    #ca = _load_required_modules()
    fname1 = dsdir+'/params.json'
    fname2 = ca.realizeFile(path=fname1)
    if not fname2:
        raise Exception('Unable to find file: '+fname1)
    if not os.path.exists(fname2):
        raise Exception('Dataset parameter file does not exist: ' + fname2)
    with open(fname2) as f:
        return json.load(f)

import mlprocessors as mlpr
import os
import time
import numpy as np
from os.path import join
from subprocess import Popen, PIPE
import shlex
import random
import string
import shutil
from spikeforest import mdaio
import spikeextractors as se
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
from mountaintools import client as mt
import json


class JRClust(mlpr.Processor):
    """
    JRClust v4 wrapper
      written by J. James Jun, May 8, 2019
      modified from `spikeforest/spikesorters/ironclust/ironclust.py`

    [Installation instruction in SpikeForest environment]
    1. Run `git clone https://github.com/JaneliaSciComp/JRCLUST`
    2. Activate conda environment for SpikeForest
    3. Create `JRCLUST_PATH` and `MDAIO_PATH`

    See: James Jun, et al. Real-time spike sorting platform for
    high-density extracellular probes with ground-truth validation and drift correction
    https://github.com/JaneliaSciComp/JRCLUST
    """

    NAME = 'JRClust'
    VERSION = '0.0.2'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    ADDITIONAL_FILES = ['*.m', '*.prm']
    CONTAINER = None
    CONTAINER_SHARE_ID = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(
        optional=True, default=-1, description='Use -1, 0, or 1, depending on the sign of the spikes in the recording')
    adjacency_radius = mlpr.FloatParameter(
        optional=True, default=50, description='')
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=4.5, description='detection threshold')
    freq_min = mlpr.FloatParameter(
        optional=True, default=300, description='Use 0 for no bandpass filtering')
    freq_max = mlpr.FloatParameter(
        optional=True, default=3000, description='Use 0 for no bandpass filtering')
    merge_thresh = mlpr.FloatParameter(
        optional=True, default=0.98, description='Threshold for automated merging')
    pc_per_chan = mlpr.IntegerParameter(
        optional=True, default=1, description='Number of principal components per channel')

    # added in version 0.2.4
    filter_type = mlpr.StringParameter(
        optional=True, default='bandpass', description='{none, bandpass, wiener, fftdiff, ndiff}')
    nDiffOrder = mlpr.FloatParameter(optional=True, default=2, description='')
    common_ref_type = mlpr.StringParameter(
        optional=True, default='none', description='{none, mean, median}')
    min_count = mlpr.IntegerParameter(
        optional=True, default=30, description='Minimum cluster size')
    fGpu = mlpr.BoolParameter(
        optional=True, default=False, description='Use GPU if available')
    fParfor = mlpr.BoolParameter(
        optional=True, default=True, description='Use parfor if available')
    feature_type = mlpr.StringParameter(
        optional=True, default='gpca', description='{gpca, pca, vpp, vmin, vminmax, cov, energy, xcov}')

    def run(self):
        jrclust_path = os.environ.get('JRCLUST_PATH', None)
        if not jrclust_path:
            raise Exception('Environment variable not set: JRCLUST_PATH')
        mdaio_path = os.environ.get('MDAIO_PATH', None)
        if not mdaio_path:
            raise Exception('Environment variable not set: MDAIO_PATH')

        tmpdir = _get_tmpdir('jrclust')

        try:
            recording = SFMdaRecordingExtractor(self.recording_dir)
            params = read_dataset_params(self.recording_dir)
            if len(self.channels) > 0:
                recording = se.SubRecordingExtractor(
                    parent_recording=recording, channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)

            all_params = dict()
            for param0 in self.PARAMETERS:
                all_params[param0.name] = getattr(self, param0.name)
            sorting = jrclust_helper(
                recording=recording,
                tmpdir=tmpdir,
                jrclust_path=jrclust_path,
                mdaio_path=mdaio_path,
                params=params,
                **all_params,
            )
            SFMdaSortingExtractor.write_sorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                if not getattr(self, '_keep_temp_files', False):
                    shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            shutil.rmtree(tmpdir)


def jrclust_helper(
        *,
        recording,  # Recording object
        tmpdir,  # Temporary working directory
        jrclust_path=None,
        mdaio_path=None,
        params=dict(),
        **kwargs):
    if jrclust_path is None:
        jrclust_path = os.getenv('JRCLUST_PATH', None)
    if mdaio_path is None:
        mdaio_path = os.getenv('MDAIO_PATH', None)
    if not jrclust_path:
        raise Exception(
            'You must either set the JRCLUST_PATH environment variable, or pass the jrclust_path parameter')
    if not mdaio_path:
        raise Exception(
            'You must either set the MDAIO_PATH environment variable, or pass the mdaio_path parameter')

    dataset_dir = os.path.join(tmpdir, 'jrclust_dataset')
    # Generate three files in the dataset directory: raw.mda, geom.csv, params.json
    SFMdaRecordingExtractor.write_recording(
        recording=recording, save_path=dataset_dir, params=params)

    samplerate = recording.get_sampling_frequency()

    print('Reading timeseries header...')
    raw_mda = os.path.join(dataset_dir, 'raw.mda')
    HH = mdaio.readmda_header(raw_mda)
    num_channels = HH.dims[0]
    num_timepoints = HH.dims[1]
    duration_minutes = num_timepoints / samplerate / 60
    print('Num. channels = {}, Num. timepoints = {}, duration = {} minutes'.format(
        num_channels, num_timepoints, duration_minutes))

    print('Creating argfile.txt...')
    txt = ''
    for key0, val0 in kwargs.items():
        txt += '{}={}\n'.format(key0, val0)
    if 'scale_factor' in params:
        txt += 'bitScaling={}\n'.format(params["scale_factor"])
    txt += 'sampleRate={}\n'.format(samplerate)
    _write_text_file(dataset_dir + '/argfile.txt', txt)

    # new method
    source_path = os.path.dirname(os.path.realpath(__file__))
    print('Running jrclust in {tmpdir}...'.format(tmpdir=tmpdir))
    cmd = '''
        addpath('{jrclust_path}', '{mdaio_path}', '{source_path}');
        try
            p_jrclust('{tmpdir}', '{dataset_dir}/raw.mda', '{dataset_dir}/geom.csv', '{tmpdir}/firings.mda', '{dataset_dir}/argfile.txt');
        catch
            fprintf('----------------------------------------');
            fprintf(lasterr());
            quit(1);
        end
        quit(0);
    '''
    cmd = cmd.format(jrclust_path=jrclust_path, tmpdir=tmpdir, dataset_dir=dataset_dir, mdaio_path=mdaio_path, source_path=source_path)

    matlab_cmd = mlpr.ShellScript(cmd, script_path=tmpdir + '/run_jrclust.m', keep_temp_files=True)
    matlab_cmd.write()

    shell_cmd = '''
        #!/bin/bash
        cd {tmpdir}
        matlab -nosplash -nodisplay -r run_jrclust
    '''.format(tmpdir=tmpdir)
    shell_cmd = mlpr.ShellScript(shell_cmd, script_path=tmpdir + '/run_jrclust.sh', keep_temp_files=True)
    shell_cmd.write(tmpdir + '/run_jrclust.sh')
    shell_cmd.start()

    retcode = shell_cmd.wait()

    if retcode != 0:
        raise Exception('jrclust returned a non-zero exit code')

    # parse output
    result_fname = tmpdir + '/firings.mda'
    if not os.path.exists(result_fname):
        raise Exception('Result file does not exist: ' + result_fname)

    firings = mdaio.readmda(result_fname)
    sorting = se.NumpySortingExtractor()
    sorting.set_times_labels(firings[1, :], firings[2, :])
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
    # ca = _load_required_modules()
    fname1 = dsdir + '/params.json'
    fname2 = mt.realizeFile(path=fname1)
    if not fname2:
        raise Exception('Unable to find file: ' + fname1)
    if not os.path.exists(fname2):
        raise Exception('Dataset parameter file does not exist: ' + fname2)
    with open(fname2) as f:
        return json.load(f)


# To be shared across sorters (2019.05.05)
def _get_tmpdir(sorter_name):
    code = ''.join(random.choice(string.ascii_uppercase) for x in range(10))
    tmpdir0 = os.environ.get('TEMPDIR', '/tmp')
    tmpdir = os.path.join(tmpdir0, '{}-tmp-{}'.format(sorter_name, code))
    # reset the output folder
    if os.path.exists(tmpdir):
        shutil.rmtree(str(tmpdir))
    else:
        os.makedirs(tmpdir)
    return tmpdir

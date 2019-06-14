import mlprocessors as mlpr
import os
import pathlib
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
import sys
import shlex
import traceback
from .install_kilosort import install_kilosort


class KiloSort(mlpr.Processor):
    """
    Kilosort wrapper for SpikeForest framework
      written by J. James Jun, May 21, 2019

    [Prerequisite]
    1. MATLAB (Tested on R2018b)
    2. CUDA Toolkit v9.1 (module load cuda/9.1.85)
    3. GCC 6.4.0 (module load gcc/6.4.0)

    [Optional: Installation instruction in SpikeForest environment]
    1. Run `git clone https://github.com/cortex-lab/KiloSort.git`
    3. In Matlab, run `CUDA/mexGPUall` to compile all CUDA codes
    4. Add `KILOSORT_PATH_DEV=...` in your .bashrc file.
    """

    NAME = 'KiloSort'
    VERSION = '0.2.3'  # wrapper VERSION
    ADDITIONAL_FILES = ['*.m']
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    CONTAINER = None
    LOCAL_MODULES = ['../../spikeforest']

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(optional=True, default=-1,
                                        description='Use -1 or 1, depending on the sign of the spikes in the recording')
    adjacency_radius = mlpr.FloatParameter(optional=True, default=-1,
                                           description='Currently unused')
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=3, description='')
    # prm_template_name=mlpr.StringParameter(optional=False,description='TODO')
    freq_min = mlpr.FloatParameter(
        optional=True, default=300, description='Use 0 for no bandpass filtering')
    freq_max = mlpr.FloatParameter(
        optional=True, default=6000, description='Use 0 for no bandpass filtering')
    merge_thresh = mlpr.FloatParameter(
        optional=True, default=0.98, description='TODO')
    pc_per_chan = mlpr.IntegerParameter(
        optional=True, default=3, description='TODO')
    Th1 = mlpr.FloatParameter(
        optional=True, default=10, description='Threshold for projections.')
    Th2 = mlpr.FloatParameter(
        optional=True, default=4, description='Threshold for projections on final pass.')
    nfilt_factor = mlpr.IntegerParameter(
        optional=True, default=4, description='Max number of assignable clusters (even during fitting) for each channel.')
    NT_fac = mlpr.IntegerParameter(
        optional=True, default=1024, description='Batch size (will be multiplied by 32).')
    minFR = mlpr.FloatParameter(default=1 / 50, optional=True,
                                description='minimum spike rate (Hz), if a cluster falls below this for too long it gets removed')

    @staticmethod
    def install():
        print('Auto-installing kilosort.')
        return install_kilosort(
            repo='https://github.com/cortex-lab/KiloSort.git',
            commit='3f33771f8fdf8c3846a7f8a75cc8c318b44ed48c'
        )

    def run(self):
        keep_temp_files = True
        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/kilosort-tmp-' + code

        try:
            recording = SFMdaRecordingExtractor(self.recording_dir)
            if len(self.channels) > 0:
                recording = se.SubRecordingExtractor(
                    parent_recording=recording, channel_ids=self.channels)
            pathlib.Path(tmpdir).mkdir(parents=True, exist_ok=True)
            sorting = kilosort_helper(
                recording=recording,
                recording_dir=self.recording_dir,
                tmpdir=tmpdir,
                detect_sign=self.detect_sign,
                adjacency_radius=self.adjacency_radius,
                detect_threshold=self.detect_threshold,
                merge_thresh=self.merge_thresh,
                freq_min=self.freq_min,
                freq_max=self.freq_max,
                pc_per_chan=self.pc_per_chan,
                Th1=self.Th1,
                Th2=self.Th2,
                nfilt_factor=self.nfilt_factor,
                NT_fac=self.NT_fac,
            )
            SFMdaSortingExtractor.write_sorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                if not keep_temp_files:
                    shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            shutil.rmtree(tmpdir)


def kilosort_helper(*,
                    recording,  # Recording object
                    tmpdir,  # Temporary working directory
                    detect_sign=-1,  # Polarity of the spikes, -1, 0, or 1
                    adjacency_radius=-1,  # Channel neighborhood adjacency radius corresponding to geom file
                    detect_threshold=5,  # Threshold for detection
                    merge_thresh=.98,  # Cluster merging threhold 0..1
                    freq_min=300,  # Lower frequency limit for band-pass filter
                    freq_max=6000,  # Upper frequency limit for band-pass filter
                    pc_per_chan=3,  # Number of pc per channel
                    Th1=10,
                    Th2=4,
                    nfilt_factor=4,
                    NT_fac=1024,
                    recording_dir=None
                    ):
    kilosort_path = os.environ.get('KILOSORT_PATH_DEV', None)
    if kilosort_path:
        print('Using kilosort from KILOSORT_PATH_DEV directory: {}'.format(kilosort_path))
    else:
        try:
            kilosort_path = KiloSort.install()
        except:
            traceback.print_exc()
            raise Exception('Problem installing kilosort. You can set the KILOSORT_PATH_DEV to force to use a particular path.')
    print('Using kilosort from: {}'.format(kilosort_path))

    source_dir = os.path.dirname(os.path.realpath(__file__))

    if recording_dir is None:
        dataset_dir = tmpdir+'/kilosort_dataset'
        recording.write_recording(dataset_dir)
    else:
        dataset_dir = recording_dir
    # Generate three files in the dataset directory: raw.mda, geom.csv, params.json
    samplerate = recording.get_sampling_frequency()

    print('Reading timeseries header...')
    HH = mdaio.readmda_header(dataset_dir + '/raw.mda')
    num_channels = HH.dims[0]
    num_timepoints = HH.dims[1]
    duration_minutes = num_timepoints / samplerate / 60
    print('Num. channels = {}, Num. timepoints = {}, duration = {} minutes'.format(
        num_channels, num_timepoints, duration_minutes))

    print('Creating argfile.txt file...')
    txt = ''
    txt += 'samplerate={}\n'.format(samplerate)
    txt += 'detect_sign={}\n'.format(detect_sign)
    txt += 'adjacency_radius={}\n'.format(adjacency_radius)
    txt += 'detect_threshold={}\n'.format(detect_threshold)
    txt += 'merge_thresh={}\n'.format(merge_thresh)
    txt += 'freq_min={}\n'.format(freq_min)
    txt += 'freq_max={}\n'.format(freq_max)
    txt += 'pc_per_chan={}\n'.format(pc_per_chan)
    txt += 'Th1={}\n'.format(Th1)
    txt += 'Th2={}\n'.format(Th2)
    txt += 'nfilt_factor={}\n'.format(nfilt_factor)
    txt += 'NT_fac={}\n'.format(NT_fac)

    _write_text_file(tmpdir+'/argfile.txt', txt)
    print('Running kilosort in {tmpdir}...'.format(tmpdir=tmpdir))
    cmd = '''
        addpath('{source_dir}');
        addpath('{source_dir}/mdaio')
        try
            p_kilosort('{ksort}', '{tmpdir}', '{raw}', '{geom}', '{firings}', '{arg}');
        catch e
            disp(getReport(e))    
            quit(1);
        end
        quit(0);
        '''
    cmd = cmd.format(source_dir=source_dir, ksort=kilosort_path,
                     tmpdir=tmpdir, raw=dataset_dir + '/raw.mda', geom=dataset_dir + '/geom.csv',
                     firings=tmpdir + '/firings.mda', arg=tmpdir + '/argfile.txt')
    matlab_cmd = mlpr.ShellScript(cmd, script_path=tmpdir + '/run_kilosort.m', keep_temp_files=True)
    matlab_cmd.write()
    shell_cmd = '''
        #!/bin/bash
        cd {tmpdir}
        echo '=====================' `date` '====================='
        matlab -nosplash -nodisplay -r run_kilosort
    '''.format(tmpdir=tmpdir)
    shell_cmd = mlpr.ShellScript(shell_cmd, script_path=tmpdir + '/run_kilosort.sh', keep_temp_files=True, log_path=tmpdir + '/run.log')
    shell_cmd.write(tmpdir + '/run_kilosort.sh')
    shell_cmd.start()
    retcode = shell_cmd.wait()

    if retcode != 0:
        print(Warning('kilosort returned a non-zero exit code'))

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

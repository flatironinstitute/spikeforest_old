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
import sys
import shlex
# import h5py


class KiloSort2(mlpr.Processor):
    NAME = 'KiloSort2'
    VERSION = '0.2.32'  # wrapper VERSION
    ADDITIONAL_FILES = ['*.m']
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    CONTAINER = None
    CONTAINER_SHARE_ID = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(
        'Use -1 or 1, depending on the sign of the spikes in the recording')
    adjacency_radius = mlpr.FloatParameter(
        'Use -1 to include all channels in every neighborhood')
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=3, description='')
    # prm_template_name=mlpr.StringParameter(optional=False,description='TODO')
    freq_min = mlpr.FloatParameter(
        optional=True, default=500, description='Use 0 for no bandpass filtering')
    freq_max = mlpr.FloatParameter(
        optional=True, default=6000, description='Use 0 for no bandpass filtering')
    merge_thresh = mlpr.FloatParameter(
        optional=True, default=0.98, description='Threshold for merging clusters.')
    pc_per_chan = mlpr.IntegerParameter(
        optional=True, default=3, description='Principal Components per channel')
    Th1 = mlpr.FloatParameter(
        optional=True, default=10, description='Threshold for projections on last pass.')
    Th2 = mlpr.FloatParameter(
        optional=True, default=4, description='Threshold for projections.')
    CAR = mlpr.IntegerParameter(
        optional=True, default=1, description='Whether to do common average referencing.')
    nfilt_factor = mlpr.IntegerParameter(
        optional=True, default=4, description='Max number of assignable clusters (even during fitting) for each channel.')
    NT_fac = mlpr.IntegerParameter(
        optional=True, default=1024, description='Batch size (will be multiplied by 32).')


    def run(self):
        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/kilosort2-tmp-' + code

        try:
            recording = SFMdaRecordingExtractor(self.recording_dir)
            if len(self.channels) > 0:
                recording = se.SubRecordingExtractor(
                    parent_recording=recording, channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
            sorting = kilosort2_helper(
                recording=recording,
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
                CAR=self.CAR,
                nfilt_factor=self.nfilt_factor,
                NT_fac=self.NT_fac
            )
            SFMdaSortingExtractor.writeSorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            # if os.path.exists(tmpdir):
            #    shutil.rmtree(tmpdir)
            raise
        # shutil.rmtree(tmpdir)


def kilosort2_helper(*,
                    recording,  # Recording object
                    tmpdir,  # Temporary working directory
                    detect_sign=-1,  # Polarity of the spikes, -1, 0, or 1
                    adjacency_radius=-1,  # Channel neighborhood adjacency radius corresponding to geom file
                    detect_threshold=5,  # Threshold for detection
                    merge_thresh=.98,  # Cluster merging threhold 0..1
                    freq_min=150,  # Lower frequency limit for band-pass filter
                    freq_max=6000,  # Upper frequency limit for band-pass filter
                    pc_per_chan=3,  # Number of pc per channel
                    Th1=10,
                    Th2=4,
                    CAR=1,
                    nfilt_factor=4,
                    NT_fac=1024,
                    KILOSORT2_PATH=None,  # github kilosort2
                    IRONCLUST_PATH=None  # github ironclust
                    ):
    if KILOSORT2_PATH is None:
        KILOSORT2_PATH = os.getenv('KILOSORT2_PATH', None)
    if not KILOSORT2_PATH:
        raise Exception(
            'You must either set the KILOSORT2_PATH environment variable, or pass the KILOSORT2_PATH parameter')

    if IRONCLUST_PATH is None:
        IRONCLUST_PATH = os.getenv('IRONCLUST_PATH', None)
    if not IRONCLUST_PATH:
        raise Exception(
            'You must either set the IRONCLUST_PATH environment variable, or pass the IRONCLUST_PATH parameter')

    source_dir = os.path.dirname(os.path.realpath(__file__))

    dataset_dir = tmpdir + '/kilosort2_dataset'
    # Generate three files in the dataset directory: raw.mda, geom.csv, params.json
    SFMdaRecordingExtractor.writeRecording(
        recording=recording, save_path=dataset_dir)

    samplerate = recording.getSamplingFrequency()

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
    txt += 'CAR={}\n'.format(CAR)
    txt += 'nfilt_factor={}\n'.format(nfilt_factor)
    txt += 'NT_fac={}\n'.format(NT_fac)
    _write_text_file(dataset_dir+'/argfile.txt', txt)

    print('Running kilosort2...')
    print('Running kilosort2 in {tmpdir}...'.format(tmpdir=tmpdir))
    logfilename = 'run.log'
    print('Logfile at {tmpdir}...'.format(tmpdir=logfilename))
    cmd = '''
addpath('{source_dir}');
try
    p_kilosort2('{ksort}', '{iclust}', '{tmpdir}', '{raw}', '{geom}', '{firings}', '{arg}');
catch e
    disp(getReport(e))
    quit(1);
end
quit(0);
        '''
    cmd = cmd.format(source_dir=source_dir, ksort=KILOSORT2_PATH, iclust=IRONCLUST_PATH, \
            tmpdir=tmpdir, raw=dataset_dir+'/raw.mda', geom=dataset_dir+'/geom.csv', \
            firings=tmpdir+'/firings.mda', arg=dataset_dir+'/argfile.txt')
    matlab_cmd = mlpr.ShellScript(cmd,script_path=tmpdir+'/run_kilosort.m',keep_temp_files=True)
    matlab_cmd.write();
    shell_cmd = '''
        #!/bin/bash
        cd {tmpdir}
        echo '=====================' `date` '=====================' >> {lf}
        matlab -nosplash -nodisplay -r run_kilosort &>> {lf}
    '''.format(tmpdir=tmpdir,lf=logfilename)
    shell_cmd = mlpr.ShellScript(shell_cmd, script_path=tmpdir+'/run_kilosort.sh', keep_temp_files=True)
    shell_cmd.write(tmpdir+'/run_kilosort.sh')
    shell_cmd.start()
    retcode = shell_cmd.wait()

    if retcode != 0:
        raise Exception('kilosort2 returned a non-zero exit code')

    # parse output
    result_fname = tmpdir + '/firings.mda'
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

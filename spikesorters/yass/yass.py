import mlprocessors as mlpr
import spikeextractors as se

import os
import time
import numpy as np
from os.path import join
from subprocess import Popen, PIPE
import shlex
import random
import string
import shutil


# yass uses negative polarity by default
class yass(mlpr.Processor):
    NAME = 'yass'
    VERSION = '0.0.1'
    # used by container to pass the env variables
    ENVIRONMENT_VARIABLES = ['NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    recording_dir = mlpr.Input('Directory of recording', directory=True)
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(description='-1, 1, or 0')
    adjacency_radius = mlpr.FloatParameter(
        optional=True, default=100, description='Channel neighborhood adjacency radius corresponding to geom file')
    template_width_ms = mlpr.FloatParameter(
        optional=True, default=3, description='Spike width in milliseconds')
    filter = mlpr.BoolParameter(optional=True, default=True)

    def run(self):
        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp')+'/yass-tmp-'+code

        num_workers = os.environ.get('NUM_WORKERS', 1)

        try:
            recording = se.MdaRecordingExtractor(self.recording_dir)
            if len(self.channels) > 0:
                recording = se.SubRecordingExtractor(
                    parent_recording=recording, channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
            sorting = yass(
                recording=recording,
                output_folder=tmpdir,
                probe_file=None,
                file_name=None,
                detect_sign=self.detect_sign,
                adjacency_radius=self.adjacency_radius,
                spike_thresh=self.spike_thresh,
                template_width_ms=self.template_width_ms,
                filter=self.filter,
                n_cores=num_workers,
            )
            se.MdaSortingExtractor.writeSorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            raise
        shutil.rmtree(tmpdir)


def yass(
    recording,
    output_folder=None,  # Temporary working directory
    probe_file=None,
    file_name=None,
    detect_sign=-1,  # -1 - 1 - 0
    template_width_ms=1,  # Spyking circus parameter
    filter=True,
    adjacency_radius=100,
    n_cores=None
):

    source_dir = os.path.dirname(os.path.realpath(__file__))

    # make output dir
    if output_folder is None:
        output_folder = 'yass'
    else:
        output_folder = join(output_folder, 'yass')
    output_folder = os.path.abspath(output_folder)
    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    # save prb file:
    if probe_file is None:
        probe_file = join_abspath_(output_folder, 'probe.npy')
    se.saveProbeFile(recording, probe_file, format='yass')

    # save binary file
    if file_name is None:
        file_name = 'raw.bin'
    bin_file = join_abspath_(output_folder, file_name)
    si.RawRecordingExtractor.writeRecording(
        recording=recording, save_path=bin_file, fReversePolarity=(detect_sign > 0), dtype=np.int16)

    # set up yass config file
    with open(join(source_dir, 'config_default.yaml'), 'r') as f:
        yass_config = f.readlines()

    # get the order
    # root_folder, recordings, geometry, dtype, sampling_rate, n_channels, spatial_radius, spike_size_ms, filter
    n_channels = recording.getNumChannels()
    sampling_rate = recording.getSamplingFrequency()

    yass_config = ''.join(yass_config).format(
        output_folder, bin_file, probe_file, 'int16', sampling_rate, n_channels, adjacency_radius, template_width_ms, filter)
    with open(join(output_folder, file_name + '.params'), 'w') as f:
        f.writelines(yass_config)

    print('Running spyking circus...')
    t_start_proc = time.time()
    if n_cores is None:
        n_cores = np.maximum(1, int(os.cpu_count()/2))

    output_folder_cmd = output_folder

    num_cores_str = ''
    if int(n_cores) > 1:
        num_cores_str = '-c {}'.format(n_cores)
    cmd = 'python2 {}\\yass {} {} '.format(
        yass_path, join(output_folder_cmd, file_name+'.yaml'), num_cores_str)

    # I think the merging step requires a gui and some user interaction. TODO: inquire about this
    # cmd_merge = 'spyking-circus {} -m merging {} '.format(join(output_folder_cmd, file_name+'.npy'), num_cores_str)
    # cmd_convert = 'spyking-circus {} -m converting'.format(join(output_folder, file_name+'.npy'))

    retcode = run_command_and_print_output(cmd)
    if retcode != 0:
        raise Exception('Spyking circus returned a non-zero exit code')

    # retcode = run_command_and_print_output(cmd_merge)
    # if retcode != 0:
    #    raise Exception('Spyking circus merging returned a non-zero exit code')
    processing_time = time.time() - t_start_proc
    print('Elapsed time: ', processing_time)
    sorting = se.yassSortingExtractor(output_folder)

    return sorting


def run_command_and_print_output(command):
    print('RUNNING: '+command)
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


def join_abspath_(path1, path2):
    path_abs = os.path.abspath(os.path.join(path1, path2))
    return path_abs

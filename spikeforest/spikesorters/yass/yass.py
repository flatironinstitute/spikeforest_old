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
from .yasssortingextractor import yassSortingExtractor
from .tools import saveProbeFile

# yass uses negative polarity by default


class YASS(mlpr.Processor):
    NAME = 'YASS'
    VERSION = '0.1.0'
    # used by container to pass the env variables
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    ADDITIONAL_FILES = ['*.yaml']

    # The following container uses python 2
    # CONTAINER = 'sha1://087767605e10761331699dda29519444bbd823f4/02-12-2019/yass.simg'
    
    # this one uses python 3
    CONTAINER = 'sha1://348be6fb09807c774e469c3aeabf4bca867c039f/03-29-2019/yass.simg'
    
    # CONTAINER_SHARE_ID = '69432e9201d0'  # place to look for container

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings_out = mlpr.Output('Output firings file')
    #paramfile_out = mlpr.Output('YASS yaml config file')

    detect_sign = mlpr.IntegerParameter(description='-1, 1, or 0')
    adjacency_radius = mlpr.FloatParameter(
        optional=True, default=100, description='Channel neighborhood adjacency radius corresponding to geom file')
    template_width_ms = mlpr.FloatParameter(
        optional=True, default=3, description='Spike width in milliseconds')
    filter = mlpr.BoolParameter(optional=True, default=True)

    def run(self):
        from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
        import spikeextractors as se

        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp')+'/yass-tmp-'+code

        #num_workers = os.environ.get('NUM_WORKERS', 1)
        #print('num_workers: {}'.format(num_workers))
        try:
            recording = SFMdaRecordingExtractor(self.recording_dir)
            if len(self.channels) > 0:
                recording = se.SubRecordingExtractor(
                    parent_recording=recording, channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
            sorting, yaml_file = yass_helper(
                recording=recording,
                output_folder=tmpdir,
                probe_file=None,
                file_name=None,
                detect_sign=self.detect_sign,
                adjacency_radius=self.adjacency_radius,
                template_width_ms=self.template_width_ms,
                filter=self.filter)
            SFMdaSortingExtractor.writeSorting(
                sorting=sorting, save_path=self.firings_out)
            #shutil.copyfile(yaml_file, self.paramfile_out)
        except:
            if os.path.exists(tmpdir):
                shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            shutil.rmtree(tmpdir)


def yass_helper(
        recording,
        output_folder=None,  # Temporary working directory
        probe_file=None,
        file_name=None,
        detect_sign=-1,  # -1 - 1 - 0
        template_width_ms=1,  # yass parameter
        filter=True,
        adjacency_radius=100):

    from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor

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
    saveProbeFile(recording, probe_file, format='yass')

    # save binary file
    if file_name is None:
        file_name = 'raw.bin'
    bin_file = join_abspath_(output_folder, file_name)
    # print('bin_file:{}'.format(bin_file))
    writeRecording_(recording=recording, save_path=bin_file,
                    fReversePolarity=(detect_sign > 0), dtype=np.float32, scale_factor=1)
    #print('bin_file exists? {}'.format(os.path.exists(bin_file)))

    # set up yass config file
    print(source_dir)
    with open(join(source_dir, 'config_default.yaml'), 'r') as f:
        yass_config = f.read()

    # get the order
    # root_folder, recordings, geometry, dtype, sampling_rate, n_channels, spatial_radius, spike_size_ms, filter
    n_channels = recording.getNumChannels()
    sampling_rate = recording.getSamplingFrequency()

    # print('sampling_rate={}'.format(sampling_rate))

    yaml_file = join(output_folder, file_name + '.yaml')
    yass_config = yass_config.format(
        output_folder, bin_file, probe_file, 'single', int(sampling_rate), n_channels, adjacency_radius, template_width_ms, filter)
    with open(yaml_file, 'w') as f:
        f.write(yass_config)

    with open(yaml_file) as ff:
        print('YASS CONFIG:')
        print(ff.read())

    print('Running yass...')
    t_start_proc = time.time()

    yass_path = '/usr/local/bin'
    num_cores_str = ''
    # cmd = 'python2 {}/yass {} {} '.format(
    #    yass_path, join(output_folder, file_name+'.yaml'), num_cores_str)
    cmd = 'yass {}'.format(join(output_folder, file_name+'.yaml'))

    retcode = run_command_and_print_output(cmd)
    if retcode != 0:
        raise Exception('yass returned a non-zero exit code')

    # retcode = run_command_and_print_output(cmd_merge)
    # if retcode != 0:
    #    raise Exception('yass merging returned a non-zero exit code')
    processing_time = time.time() - t_start_proc
    print('Elapsed time: ', processing_time)
    sorting = yassSortingExtractor(join_abspath_(output_folder, 'tmp'))

    return sorting, yaml_file


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


def writeRecording_(recording, save_path, dtype=None, transpose=False, fReversePolarity=False, scale_factor=1):
    #save_path = Path(save_path)
    print('writeRecording2: {}'.format(str(save_path)))

    if dtype == None:
        dtype = np.float32
    np_Wav = np.array(recording.getTraces(), dtype=dtype)
    if transpose:
        np_Wav = np.transpose(np_Wav)
    if fReversePolarity:
        np_Wav = np_Wav * -1
    np_Wav = np_Wav * scale_factor
    with open(save_path, 'wb') as f:
        np.ravel(np_Wav, order='F').tofile(f)

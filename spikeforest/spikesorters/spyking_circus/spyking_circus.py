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
import spikeextractors as se
from .tools import saveProbeFile
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
from .spykingcircussortingextractor import SpykingCircusSortingExtractor

class SpykingCircus(mlpr.Processor):
    NAME = 'SpykingCircus'
    VERSION = '0.2.2'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    ADDITIONAL_FILES = ['*.params']
    CONTAINER = 'sha1://8daaf751fc3f40dd6f86696e8fcb675bcf1ba212/03-29-2019/spyking_circus.simg'
    # CONTAINER_SHARE_ID = '69432e9201d0'  # place to look for container

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(description='-1, 1, or 0')
    adjacency_radius = mlpr.FloatParameter(
        optional=True, default=100, description='Channel neighborhood adjacency radius corresponding to geom file')
    spike_thresh = mlpr.FloatParameter(
        optional=True, default=6, description='Threshold for detection')
    template_width_ms = mlpr.FloatParameter(
        optional=True, default=3, description='Spyking circus parameter')
    filter = mlpr.BoolParameter(optional=True, default=True)
    whitening_max_elts = mlpr.IntegerParameter(
        optional=True, default=1000, description='I believe it relates to subsampling and affects compute time')
    clustering_max_elts = mlpr.IntegerParameter(
        optional=True, default=10000, description='I believe it relates to subsampling and affects compute time')

    def run(self):
        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp')+'/spyking-circus-tmp-'+code

        num_workers = os.environ.get('NUM_WORKERS', 1)

        try:
            recording = SFMdaRecordingExtractor(self.recording_dir)
            if len(self.channels) > 0:
                recording = se.SubRecordingExtractor(
                    parent_recording=recording, channel_ids=self.channels)
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
            sorting = spyking_circus(
                recording=recording,
                output_folder=tmpdir,
                probe_file=None,
                file_name=None,
                detect_sign=self.detect_sign,
                adjacency_radius=self.adjacency_radius,
                spike_thresh=self.spike_thresh,
                template_width_ms=self.template_width_ms,
                filter=self.filter,
                merge_spikes=True,
                n_cores=num_workers,
                electrode_dimensions=None,
                whitening_max_elts=self.whitening_max_elts,
                clustering_max_elts=self.clustering_max_elts,
            )
            SFMdaSortingExtractor.writeSorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if not getattr(self, '_keep_temp_files', False):
                if os.path.exists(tmpdir):
                    shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            shutil.rmtree(tmpdir)


def spyking_circus(
    recording,
    output_folder=None,  # Temporary working directory
    probe_file=None,
    file_name=None,
    detect_sign=-1,  # -1 - 1 - 0
    adjacency_radius=100,  # Channel neighborhood adjacency radius corresponding to geom file
    spike_thresh=6,  # Threshold for detection
    template_width_ms=3,  # Spyking circus parameter
    filter=True,
    merge_spikes=True,
    n_cores=None,
    electrode_dimensions=None,
    whitening_max_elts=1000,  # I believe it relates to subsampling and affects compute time
    # I believe it relates to subsampling and affects compute time
    clustering_max_elts=10000,
    singularity_container=None
):
    if not singularity_container:
        try:
            import circus # pylint: disable=import-error
        except ModuleNotFoundError:
            raise ModuleNotFoundError("\nTo use Spyking-Circus, install spyking-circus: \n\n"
                                      "\npip install spyking-circus"
                                      "\nfor ubuntu install openmpi: "
                                      "\nsudo apt install libopenmpi-dev"
                                      "\nMore information on Spyking-Circus at: "
                                      "\nhttps://spyking-circus.readthedocs.io/en/latest/")
    source_dir = os.path.dirname(os.path.realpath(__file__))

    if output_folder is None:
        output_folder = 'spyking_circus'
    else:
        output_folder = join(output_folder, 'spyking_circus')
    output_folder = os.path.abspath(output_folder)

    if not os.path.isdir(output_folder):
        os.makedirs(output_folder)

    # save prb file:
    if probe_file is None:
        saveProbeFile(recording, join(output_folder, 'probe.prb'), format='spyking_circus', radius=adjacency_radius,
                         dimensions=electrode_dimensions)
        probe_file = join(output_folder, 'probe.prb')
    # save binary file
    if file_name is None:
        file_name = 'recording'
    elif file_name.endswith('.npy'):
        file_name = file_name[file_name.find('.npy')]
    np.save(join(output_folder, file_name),
            recording.getTraces().astype('float32', order='F'))

    if detect_sign < 0:
        detect_sign = 'negative'
    elif detect_sign > 0:
        detect_sign = 'positive'
    else:
        detect_sign = 'both'

    # set up spykingcircus config file
    with open(join(source_dir, 'config_default.params'), 'r') as f:
        circus_config = f.read()
    if merge_spikes:
        auto = 1e-5
    else:
        auto = 0
    circus_config = circus_config.format(
        float(recording.getSamplingFrequency()
              ), probe_file, template_width_ms, spike_thresh, detect_sign, filter,
        whitening_max_elts, clustering_max_elts, auto
    )
    params_file = join(output_folder, file_name + '.params')
    with open(params_file, 'w') as f:
        f.write(circus_config)

    # with open(params_file) as ff:
    #    print('CIRCUS CONFIG:')
    #    print(ff.read())

    print('Running spyking circus...')
    t_start_proc = time.time()
    if n_cores is None:
        n_cores = np.maximum(1, int(os.cpu_count()/2))

    output_folder_cmd = output_folder
    if singularity_container:
        output_folder_cmd = '/output_folder'

    num_cores_str = ''
    if int(n_cores) > 1:
        num_cores_str = '-c {}'.format(n_cores)
    cmd = 'spyking-circus {} {} '.format(
        join(output_folder_cmd, file_name+'.npy'), num_cores_str)

    # I think the merging step requires a gui and some user interaction. TODO: inquire about this
    # cmd_merge = 'spyking-circus {} -m merging {} '.format(join(output_folder_cmd, file_name+'.npy'), num_cores_str)
    # cmd_convert = 'spyking-circus {} -m converting'.format(join(output_folder, file_name+'.npy'))

    if singularity_container:
        cmd = 'singularity exec --contain -e -B {}:{} -B /tmp:/tmp {} bash -c "{}"'.format(
            output_folder, output_folder_cmd, singularity_container, cmd)
        # cmd_merge='singularity exec --contain -e -B {}:{} -B /tmp:/tmp {} bash -c "{}"'.format(output_folder,output_folder_cmd,singularity_container,cmd_merge)

    retcode = run_command_and_print_output(cmd)
    if retcode != 0:
        raise Exception('Spyking circus returned a non-zero exit code')

    # retcode = run_command_and_print_output(cmd_merge)
    # if retcode != 0:
    #    raise Exception('Spyking circus merging returned a non-zero exit code')
    processing_time = time.time() - t_start_proc
    print('Elapsed time: ', processing_time)
    sorting = SpykingCircusSortingExtractor(join(output_folder, file_name))

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

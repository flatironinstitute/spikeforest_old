from pathlib import Path

import mlprocessors as mlpr
import spikeextractors as se
from .sfmdaextractors import SFMdaRecordingExtractor, SFMdaSortingExtractor
import os
import time
import random
import string
import shutil
import sys
import shlex
import json
from mountaintools import client as mt
from subprocess import Popen, PIPE, CalledProcessError, call


class Klusta(mlpr.Processor):
    """

    Installation instruction
        >>> pip install Cython h5py tqdm
        >>> pip install click klusta klustakwik2

    More information on klusta at:
      * https://github.com/kwikteam/phy"
      * https://github.com/kwikteam/klusta

    """

    NAME = 'Klusta'
    VERSION = '0.1.1'  # wrapper VERSION
    ADDITIONAL_FILES = ['*.prm']
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    CONTAINER = 'sha1://6d76f22e3b4eff52b430ef4649a8802f7da9e0ec/2019-05-13/klusta.simg'
    CONTAINER_SHARE_ID = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')
    channels = mlpr.IntegerListParameter(optional=True, default=[],
                                         description='List of channels to use.')
    adjacency_radius = mlpr.FloatParameter(optional=True, default=None, description='')
    detect_sign = mlpr.FloatParameter(optional=True, default=-1, description='')
    threshold_strong_std_factor = mlpr.FloatParameter(optional=True, default=5, description='')
    threshold_weak_std_factor = mlpr.FloatParameter(optional=True, default=2, description='')
    n_features_per_channel = mlpr.IntegerParameter(optional=True, default=3, description='')
    num_starting_clusters = mlpr.IntegerParameter(optional=True, default=3, description='')
    extract_s_before = mlpr.IntegerParameter(optional=True, default=16, description='')
    extract_s_after = mlpr.IntegerParameter(optional=True, default=32, description='')

    def run(self):
        try:
            import klusta
            import klustakwik2
            HAVE_KLUSTA = True
        except ImportError:
            HAVE_KLUSTA = False

        if not HAVE_KLUSTA:
            raise Exception('Klusta kwik is not installed.')

        # alias to params
        p = {
            'probe_file': None,
            'pca_n_waveforms_max': 10000,
        }
        for param0 in self.PARAMETERS:  # pylint: disable=no-member
            p[param0.name] = getattr(self, param0.name)
        source_dir = Path(__file__).parent

        tmpdir = Path(_get_tmpdir('klusta'))

        # source file
        recording = SFMdaRecordingExtractor(self.recording_dir)
        if len(self.channels) > 0:
            recording = se.SubRecordingExtractor(
                parent_recording=recording, channel_ids=self.channels)

        # if isinstance(recording, se.BinDatRecordingExtractor) and recording._frame_first and\
        #                 recording._timeseries.offset == 0:
        #     # no need to copy
        #     raw_filename = str(recording._datfile)
        #     raw_filename = raw_filename.replace('.dat', '')
        #     dtype = recording._timeseries.dtype.str
        #     nb_chan = len(recording._channels)
        # else:
        # save binary file (chunk by hcunk) into a new file
        raw_filename = tmpdir / 'recording'
        n_chan = recording.get_num_channels()
        chunksize = 2**24 // n_chan
        dtype = 'int16'
        se.write_binary_dat_format(recording, raw_filename, time_axis=0, dtype=dtype, chunksize=chunksize)

        # save prb file:
        if p['probe_file'] is None:
            p['probe_file'] = tmpdir / 'probe.prb'
            se.save_probe_file(recording, p['probe_file'], format='klusta', radius=p['adjacency_radius'])

        if p['detect_sign'] < 0:
            detect_sign = 'negative'
        elif p['detect_sign'] > 0:
            detect_sign = 'positive'
        else:
            detect_sign = 'both'

        # set up klusta config file
        with (source_dir / 'config_default.prm').open('r') as f:
            klusta_config = f.readlines()

        # Note: should use format with dict approach here
        klusta_config = ''.join(klusta_config).format(raw_filename,
                                                      p['probe_file'], float(recording.get_sampling_frequency()),
                                                      recording.get_num_channels(), "'{}'".format(dtype),
                                                      p['threshold_strong_std_factor'], p['threshold_weak_std_factor'], "'" + detect_sign + "'",
                                                      p['extract_s_before'], p['extract_s_after'], p['n_features_per_channel'],
                                                      p['pca_n_waveforms_max'], p['num_starting_clusters']
                                                      )

        with (tmpdir / 'config.prm').open('w') as f:
            f.writelines(klusta_config)

        try:
            sorting = klusta_helper(tmpdir=tmpdir)
            SFMdaSortingExtractor.write_sorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                if not getattr(self, '_keep_temp_files', False):
                    shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            shutil.rmtree(tmpdir)


def klusta_helper(*, tmpdir):  # all mlpr parameters
    cmd = 'klusta {} --overwrite'.format(tmpdir / 'config.prm')

    _call_command(cmd)
    if not (tmpdir / 'recording.kwik').is_file():
        raise Exception('Klusta did not run successfully')
    sorting = se.KlustaSortingExtractor(tmpdir / 'recording.kwik')
    return sorting


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


def _run_command_and_print_output(command):
    command_list = shlex.split(command, posix="win" not in sys.platform)
    with Popen(command_list, stdout=PIPE, stderr=PIPE) as process:
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


def _run_command_and_print_output_split(command_list):
    with Popen(command_list, stdout=PIPE, stderr=PIPE) as process:
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


def _call_command(command):
    command_list = shlex.split(command, posix="win" not in sys.platform)
    try:
        call(command_list)
    except CalledProcessError as e:
        raise Exception(e.output)


def _call_command_split(command_list):
    try:
        call(command_list)
    except CalledProcessError as e:
        raise Exception(e.output)

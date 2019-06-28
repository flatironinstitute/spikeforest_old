from pathlib import Path

import mlprocessors as mlpr
import spikeextractors as se
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
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
import spikesorters as sorters


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
    VERSION = '0.2.0'  # wrapper VERSION
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    # CONTAINER = 'sha1://6d76f22e3b4eff52b430ef4649a8802f7da9e0ec/2019-05-13/klusta.simg'
    CONTAINER = 'sha1://182ff734d38e2ece30ed751de55807b0a8359959/2019-06-28/klusta.simg'
    LOCAL_MODULES = ['../../spikeforest']

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')
    adjacency_radius = mlpr.FloatParameter(optional=True, default=None, description='')
    detect_sign = mlpr.FloatParameter(optional=True, default=-1, description='')
    threshold_strong_std_factor = mlpr.FloatParameter(optional=True, default=5, description='')
    threshold_weak_std_factor = mlpr.FloatParameter(optional=True, default=2, description='')
    n_features_per_channel = mlpr.IntegerParameter(optional=True, default=3, description='')
    num_starting_clusters = mlpr.IntegerParameter(optional=True, default=3, description='')
    extract_s_before = mlpr.IntegerParameter(optional=True, default=16, description='')
    extract_s_after = mlpr.IntegerParameter(optional=True, default=32, description='')

    def run(self):
        print('Klusta......')
        recording = SFMdaRecordingExtractor(self.recording_dir)

        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/klusta-' + code

        sorter = sorters.KlustaSorter(
            recording=recording,
            output_folder=tmpdir,
            debug=True,
            delete_output_folder=True
        )

        sorter.set_params(
            adjacency_radius=self.adjacency_radius,
            detect_sign=self.detect_sign,
            threshold_strong_std_factor=self.threshold_strong_std_factor,
            threshold_weak_std_factor=self.threshold_weak_std_factor,
            n_features_per_channel=self.n_features_per_channel,
            num_starting_clusters=self.num_starting_clusters,
            extract_s_before=self.extract_s_before,
            extract_s_after=self.extract_s_after
        )

        # TODO: get elapsed time from the return of this run
        sorter.run()

        sorting = sorter.get_result()

        SFMdaSortingExtractor.write_sorting(
            sorting=sorting, save_path=self.firings_out)


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

from pathlib import Path

import mlprocessors as mlpr
import spikeextractors as se
import os
import random
import string
import shutil
from mountaintools import client as mt
from subprocess import Popen, PIPE, CalledProcessError, call
from typing import List


class Tridesclous(mlpr.Processor):
    """
    Installation instruction
        >>> pip install https://github.com/tridesclous/tridesclous/archive/master.zip

    More information on tridesclous at:
    * https://github.com/tridesclous/tridesclous
    * https://tridesclous.readthedocs.io

    """

    NAME = 'Tridesclous'
    VERSION = '0.2.7'  # wrapper VERSION
    ADDITIONAL_FILES: List[str] = []
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    # CONTAINER = 'sha1://9fb4a9350492ee84c8ea5d8692434ecba3cf33da/2019-05-13/tridesclous.simg'
    # CONTAINER = 'sha1://17171f85d4b35238e517ad974e2426c5990ae17a/2019-06-14/tridesclous.simg'
    # CONTAINER = 'sha1://9d13a5fb53c65b3627753e35f3af43aeeaaa14ce/2019-06-17/tridesclous.simg'
    # CONTAINER = 'sha1://bfa657d577af721954beb55ede0f0fccf9ae18bd/2019-06-18/tridesclous.simg'
    CONTAINER = 'sha1://e41f7528e7cca06c7a9ae4bf793eb08922cf5e9f/2019-11-22/tridesclous.simg'
    LOCAL_MODULES = ['../../spikeforest']

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')

    def run(self):
        print('Running Tridesclous...')
        from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
        # from spikeforest_common import autoScaleRecordingToNoiseLevel
        # import spiketoolkit as st
        import spikesorters

        code = ''.join(random.choice(string.ascii_uppercase) for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/tdc-tmp-' + code

        try:
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)

            print('Loading recording...')
            recording = SFMdaRecordingExtractor(self.recording_dir)
            # print('Auto scaling via normalize_by_quantile...')
            # recording = st.preprocessing.normalize_by_quantile(recording=recording, scale=200.0)
            # recording = autoScaleRecordingToNoiseLevel(recording, noise_level=32)

            print('Running TridesclousSorter...')
            os.environ['HS2_PROBE_PATH'] = tmpdir
            st_sorter = spikesorters.TridesclousSorter(
                recording=recording,
                output_folder=tmpdir + '/tdc_sorting_output',
                verbose=True
            )
            # setattr(st_sorter, 'debug', True)
            st_sorter
            timer = st_sorter.run()
            print('#SF-SORTER-RUNTIME#{:.3f}#'.format(timer))
            sorting = st_sorter.get_result()

            SFMdaSortingExtractor.write_sorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                if not getattr(self, '_keep_temp_files', False):
                    shutil.rmtree(tmpdir)
            raise

        if not getattr(self, '_keep_temp_files', False):
            shutil.rmtree(tmpdir)

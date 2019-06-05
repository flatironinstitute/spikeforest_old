import mlprocessors as mlpr
import os
import random
import string
import shutil
import sys
import shlex
import json
from mountaintools import client as mt


class HerdingSpikes2(mlpr.Processor):
    """
    HerdingSpikes2 wrapper for SpikeForest framework
    Calls hs2 wrapper in SpikeInterface/SpikeToolkit

    See: HILGEN, Gerrit, et al. Unsupervised spike sorting for large-scale,
    high-density multielectrode arrays. Cell reports, 2017, 18.10: 2521-2532.
    https://github.com/mhhennig/hs2
    """

    NAME = 'HS2'
    VERSION = '0.2.3'  # wrapper VERSION
    ADDITIONAL_FILES = []
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    # CONTAINER = 'sha1://d140fc9b43b98a5f70a538970bc037b5b35fefd8/2019-05-08/herdingspikes2.simg'
    # CONTAINER = 'sha1://b3209735e078abe212dfa508e267786382d28473/2019-05-30/herdingspikes2.simg'
    CONTAINER = 'sha1://57b5bf971d44c5333a07cae1a8c188df6eb0e9a1/2019-06-05/herdingspikes2.simg'
    LOCAL_MODULES = ['../../spikeforest', '../../spikeforest_common']

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')

    def run(self):
        from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
        from spikeforest_common import autoScaleRecordingToNoiseLevel
        import spiketoolkit as st

        clustering_n_jobs = os.environ.get('NUM_WORKERS', None)
        if clustering_n_jobs is not None:
            clustering_n_jobs = int(clustering_n_jobs)

        code = ''.join(random.choice(string.ascii_uppercase) for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/hs2-tmp-' + code

        try:
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)

            recording = SFMdaRecordingExtractor(self.recording_dir)
            # print('Auto scaling via normalize_by_quantile...')
            # recording = st.preprocessing.normalize_by_quantile(recording=recording, scale=200.0)
            # recording = autoScaleRecordingToNoiseLevel(recording, noise_level=32)

            print('Running HerdingspikesSorter...')
            os.environ['HS2_PROBE_PATH'] = tmpdir
            st_sorter = st.sorters.HerdingspikesSorter(
                recording=recording,
                output_folder=tmpdir + '/hs2_sorting_output'
            )
            print('Using builtin bandpass and normalisation')
            hs2_par = st_sorter.default_params()
            hs2_par['filter'] = True
            hs2_par['pre_scale'] = True
            st_sorter.set_params(**hs2_par)
            if clustering_n_jobs is not None:
                st_sorter.set_params(clustering_n_jobs=clustering_n_jobs)
            st_sorter.run()
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

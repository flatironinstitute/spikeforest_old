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

try:
    import herdingspikes as hs
    HAVE_HS = True
except ImportError:
    HAVE_HS = False


class HerdingSpikes2(mlpr.Processor):
    """
    HerdingSpikes2 wrapper for SpikeForest framework
      written by J. James Jun, May 3, 2019
      modified from `spiketoolkit/sorters/HerdingSpikesSorter`
      to be made compatible with SpikeForest

    [Installation instruction in SpikeForest environment]
    1. Run `git clone https://github.com/jamesjun/hs2`
      Note that James Jun forked a new version to make it compatible with singularity container.
      Original code was creating folders under its source directory which is ready-only in SpikeForest containers.
    2. Activate conda environment for SpikeForest
    3. Run `pip install joblib`
    4. Run `python setup.py develop` in herdingspikes2 doretory
    5. Create `herdingspikes/probes` and `herdingspikes/probe_info` folders

    HerdingSpikes is a sorter based on estimated spike location, developed by
    researchers at the University of Edinburgh. It's a fast and scalable choice.

    See: HILGEN, Gerrit, et al. Unsupervised spike sorting for large-scale,
    high-density multielectrode arrays. Cell reports, 2017, 18.10: 2521-2532.
    https://github.com/mhhennig/hs2
    """

    NAME = 'HS2'
    VERSION = '0.0.5'  # wrapper VERSION
    ADDITIONAL_FILES = []
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    CONTAINER = 'sha1://d140fc9b43b98a5f70a538970bc037b5b35fefd8/2019-05-08/herdingspikes2.simg'
    # CONTAINER = None
    CONTAINER_SHARE_ID = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')
    channels = mlpr.IntegerListParameter(optional=True, default=[],
                                         description='List of channels to use.')
    clustering_bandwidth = mlpr.FloatParameter(optional=True, default=5, description='')
    clustering_alpha = mlpr.FloatParameter(optional=True, default=5, description='')
    left_cutout_time = mlpr.FloatParameter(description='', optional=True, default=0.2)
    right_cutout_time = mlpr.FloatParameter(description='', optional=True, default=1)
    detection_threshold = mlpr.FloatParameter(optional=True, default=26, description='')
    clustering_bin_seeding = mlpr.BoolParameter(optional=True, default=True, description='')
    clustering_min_bin_freq = mlpr.FloatParameter(optional=True, default=8, description='')
    pca_ncomponents = mlpr.IntegerParameter(optional=True, default=2, description='')

    # extra_probe_params
    inner_radius, neighbor_radius, event_length, peak_jitter = \
        [mlpr.FloatParameter(optional=True, default=_x, description='') for _x in
            [75, 80, .2, .2]]
    # extra_detection_params
    maa, ahpthr, amp_evaluation_time, spk_evaluation_time = \
        [mlpr.FloatParameter(optional=True, default=_x, description='') for _x in
            [0, 0, .05, 1]]

    def run(self):
        recording = SFMdaRecordingExtractor(self.recording_dir)
        clustering_n_jobs = int(os.environ.get('NUM_WORKERS', None))
        tmpdir = _get_tmpdir('herdingspikes2')

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
            sorting = hs2_helper(
                recording=recording,
                tmpdir=tmpdir,
                params=params,
                clustering_n_jobs=clustering_n_jobs,
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


def hs2_helper(
        *,
        recording,  # Recording object
        tmpdir,  # Temporary working directory
        params,  # dataset parameters
        clustering_n_jobs,  # number of workers
        **kwargs):  # all mlpr parameters

    extra_probe_params = {
        'inner_radius': kwargs['inner_radius'],
        'neighbor_radius': kwargs['neighbor_radius'],
        'event_length': kwargs['event_length'],
        'peak_jitter': kwargs['peak_jitter'],
    }
    extra_detection_params = {
        'to_localize': True,
        'num_com_centers': 1,
        'maa': kwargs['maa'],
        'ahpthr': kwargs['ahpthr'],
        'out_file_name': "HS2_detected",
        'decay_filtering': False,
        'save_all': False,
        'amp_evaluation_time': kwargs['amp_evaluation_time'],
        'spk_evaluation_time': kwargs['spk_evaluation_time'],
    }
    extra_pca_params = {
        'pca_ncomponents': kwargs['pca_ncomponents'],
        'pca_whiten': True,
    }

    os.environ['HS2_PROBE_PATH'] = tmpdir

    # this should have its name changed
    Probe = hs.probe.RecordingExtractor(
        recording,
        **extra_probe_params)

    H = hs.HSDetection(Probe, file_directory_name=str(tmpdir),
                       left_cutout_time=kwargs['left_cutout_time'],
                       right_cutout_time=kwargs['right_cutout_time'],
                       threshold=kwargs['detection_threshold'],
                       **extra_detection_params)

    H.DetectFromRaw(load=True, tInc=1000000)

    sorted_file = os.path.join(tmpdir, 'HS2_sorted.hdf5')
    if(not H.spikes.empty):
        C = hs.HSClustering(H)
        C.ShapePCA(**extra_pca_params)
        C.CombinedClustering(
            alpha=kwargs['clustering_alpha'],
            cluster_subset=None,
            bandwidth=kwargs['clustering_bandwidth'],
            bin_seeding=kwargs['clustering_bin_seeding'],
            n_jobs=clustering_n_jobs,
            min_bin_freq=kwargs['clustering_min_bin_freq'])
    else:
        C = hs.HSClustering(H)

    print('Saving to ' + sorted_file)
    C.SaveHDF5(sorted_file)

    sorting = se.HS2SortingExtractor(sorted_file)
    return sorting


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
    tmpdir = os.path.join(tmpdir0,  '{}-tmp-{}'.format(sorter_name, code))
    # reset the output folder
    if os.path.exists(tmpdir):
        shutil.rmtree(str(tmpdir))
    else:
        os.makedirs(tmpdir)
    return tmpdir
import mlprocessors as mlpr
import spikeextractors as se
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor, mdaio
import os, time, random, string, shutil, sys, shlex, json
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
    1. Run `git clone https://github.com/mhhennig/hs2`
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
    VERSION = '0.0.1'  # wrapper VERSION
    ADDITIONAL_FILES = []
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    CONTAINER = None
    CONTAINER_SHARE_ID = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')
    adjacency_radius = mlpr.FloatParameter('Use -1 to include all channels in every neighborhood')
    channels = mlpr.IntegerListParameter(
        description='List of channels to use.', optional=True, default=[])
    clustering_bandwidth = mlpr.FloatParameter(
        optional=True, default=6.0, description='')
    clustering_alpha = mlpr.FloatParameter(
        optional=True, default=6.0, description='')
    clustering_bin_seeding = mlpr.BoolParameter(
        optional=True, default=False, description='Use GPU if available')
    cutout_start = mlpr.FloatParameter(
        description='', optional=True, default=10)
    cutout_end = mlpr.FloatParameter(
        description='', optional=True, default=30)
    detection_threshold = mlpr.FloatParameter(
        description='', optional=True, default=20)
    probe_masked_channels = mlpr.IntegerListParameter(
        description='', optional=True, default=[])

    def run(self):
        recording = SFMdaRecordingExtractor(self.recording_dir)
        clustering_n_jobs = os.environ.get('NUM_WORKERS', None)

        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + \
                                '/herdingspikes2-tmp-' + code

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
            SFMdaSortingExtractor.writeSorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                if not getattr(self, '_keep_temp_files', False):
                    shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            pass


def hs2_helper(
        *,
        recording,  # Recording object
        tmpdir,  # Temporary working directory
        params,  # dataset parameters
        clustering_n_jobs,  # number of workers
        **kwargs):  # all mlpr parameters

    extra_probe_params = {
        'inner_radius': kwargs['adjacency_radius'],
        'neighbor_radius': kwargs['adjacency_radius'],
        #'event_length': 0.5,
        #'peak_jitter': 0.2
    }
    extra_detection_params = {
        'to_localize': True,
        'num_com_centers': 1,
        'maa': 0,
        'ahpthr': 0,
        'out_file_name': "HS2_detected",
        'decay_filtering': False,
        'save_all': False,
        #'amp_evaluation_time': 0.4,
        #'spk_evaluation_time': 1.7
    }
    extra_pca_params = {
        'pca_ncomponents': 2,
        'pca_whiten': True
    }

    # this should have its name changed
    Probe = hs.probe.RecordingExtractor(
        recording, masked_channels=kwargs['probe_masked_channels'],
        **extra_probe_params)

    H = hs.HSDetection(Probe, file_directory_name=str(tmpdir),
                       cutout_start=kwargs['cutout_start'],
                       cutout_end=kwargs['cutout_end'],
                       threshold=kwargs['detection_threshold'],
                       **extra_detection_params)

    H.DetectFromRaw(load=True)

    C = hs.HSClustering(H)
    C.ShapePCA(**extra_pca_params)
    C.CombinedClustering(bandwidth=kwargs['clustering_bandwidth'],
                           alpha=kwargs['clustering_alpha'],
                           n_jobs=clustering_n_jobs,
                           bin_seeding=kwargs['clustering_bin_seeding'])

    sorted_file = os.path.join(tmpdir, 'HS2_sorted.hdf5')
    if(not H.spikes.empty):
        C = hs.HSClustering(H)
        C.ShapePCA(**extra_pca_params)
        C.CombinedClustering(alpha=kwargs['clustering_alpha'],
                                cluster_subset=None,
                                bandwidth=kwargs['clustering_bandwidth'],
                                bin_seeding=kwargs['clustering_bin_seeding'],
                                n_jobs=clustering_n_jobs,
                                )
        C.SaveHDF5(sorted_file)
    else:
        C = hs.HSClustering(H)
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

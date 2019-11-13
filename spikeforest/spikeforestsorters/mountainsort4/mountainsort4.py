import mlprocessors as mlpr
import os
import sys
from .bandpass_filter import bandpass_filter
import string
from .whiten import whiten
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
import random


class MountainSort4(mlpr.Processor):
    NAME = 'MountainSort4'
    VERSION = '4.3.1'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    # CONTAINER = 'sha1://e06fee7f72f6b66d80d899ebc08e7c39e5a2458e/2019-05-06/mountainsort4.simg'
    CONTAINER = 'sha1://8743ff094a26bdedd16f36209a05333f1f82fbd8/2019-06-26/mountainsort4.simg'
    LOCAL_MODULES = ['../../spikeforest']

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(
        'Use -1, 0, or 1, depending on the sign of the spikes in the recording')
    adjacency_radius = mlpr.FloatParameter(
        'Use -1 to include all channels in every neighborhood')
    freq_min = mlpr.FloatParameter(
        optional=True, default=300, description='Use 0 for no bandpass filtering')
    freq_max = mlpr.FloatParameter(
        optional=True, default=6000, description='Use 0 for no bandpass filtering')
    whiten = mlpr.BoolParameter(optional=True, default=True,
                                description='Whether to do channel whitening as part of preprocessing')
    clip_size = mlpr.IntegerParameter(
        optional=True, default=50, description='')
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=3, description='')
    detect_interval = mlpr.IntegerParameter(
        optional=True, default=10, description='Minimum number of timepoints between events detected on the same channel')
    noise_overlap_threshold = mlpr.FloatParameter(
        optional=True, default=0.15, description='Use None for no automated curation')

    def run(self):
        # from spikeinterface/spikesorters
        import spikesorters as sorters

        print('MountainSort4......')
        recording = SFMdaRecordingExtractor(self.recording_dir)
        num_workers = os.environ.get('NUM_WORKERS', None)
        if num_workers:
            num_workers = int(num_workers)

        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/mountainsort4-' + code

        sorter = sorters.Mountainsort4Sorter(
            recording=recording,
            output_folder=tmpdir,
            debug=True,
            delete_output_folder=True
        )

        sorter.set_params(
            detect_sign=self.detect_sign,
            adjacency_radius=self.adjacency_radius,
            clip_size=self.clip_size,
            detect_threshold=self.detect_threshold,
            detect_interval=self.detect_interval,
            num_workers=num_workers,
            curation=False,
            whiten=True,
            filter=True,
            freq_min=self.freq_min,
            freq_max=self.freq_max
        )

        # TODO: get elapsed time from the return of this run
        sorter.run()

        sorting = sorter.get_result()

        SFMdaSortingExtractor.write_sorting(
            sorting=sorting, save_path=self.firings_out)


class MountainSort4Old(mlpr.Processor):
    NAME = 'MountainSort4'
    VERSION = '4.3.0'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    CONTAINER = 'sha1://e06fee7f72f6b66d80d899ebc08e7c39e5a2458e/2019-05-06/mountainsort4.simg'
    # CONTAINER = 'sha1://8743ff094a26bdedd16f36209a05333f1f82fbd8/2019-06-26/mountainsort4.simg'
    LOCAL_MODULES = ['../../spikeforest']

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(
        'Use -1, 0, or 1, depending on the sign of the spikes in the recording')
    adjacency_radius = mlpr.FloatParameter(
        'Use -1 to include all channels in every neighborhood')
    freq_min = mlpr.FloatParameter(
        optional=True, default=300, description='Use 0 for no bandpass filtering')
    freq_max = mlpr.FloatParameter(
        optional=True, default=6000, description='Use 0 for no bandpass filtering')
    whiten = mlpr.BoolParameter(optional=True, default=True,
                                description='Whether to do channel whitening as part of preprocessing')
    clip_size = mlpr.IntegerParameter(
        optional=True, default=50, description='')
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=3, description='')
    detect_interval = mlpr.IntegerParameter(
        optional=True, default=10, description='Minimum number of timepoints between events detected on the same channel')
    noise_overlap_threshold = mlpr.FloatParameter(
        optional=True, default=0.15, description='Use None for no automated curation')

    def run(self):
        from .bandpass_filter import bandpass_filter
        from .whiten import whiten

        import ml_ms4alg

        print('MountainSort4......')
        recording = SFMdaRecordingExtractor(self.recording_dir)
        num_workers = os.environ.get('NUM_WORKERS', None)
        if num_workers:
            num_workers = int(num_workers)

        # Bandpass filter
        if self.freq_min or self.freq_max:
            recording = bandpass_filter(
                recording=recording, freq_min=self.freq_min, freq_max=self.freq_max)

        # Whiten
        if self.whiten:
            recording = whiten(recording=recording)

        # Sort
        sorting = ml_ms4alg.mountainsort4(
            recording=recording,
            detect_sign=self.detect_sign,
            adjacency_radius=self.adjacency_radius,
            clip_size=self.clip_size,
            detect_threshold=self.detect_threshold,
            detect_interval=self.detect_interval,
            num_workers=num_workers
        )

        # Curate
        # if self.noise_overlap_threshold is not None:
        #    sorting=ml_ms4alg.mountainsort4_curation(
        #      recording=recording,
        #      sorting=sorting,
        #      noise_overlap_threshold=self.noise_overlap_threshold
        #    )        

        SFMdaSortingExtractor.write_sorting(
            sorting=sorting, save_path=self.firings_out)


class MountainSort4TestError(mlpr.Processor):
    NAME = 'MountainSort4'
    VERSION = '4.2.0'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    # CONTAINER = 'sha1://e06fee7f72f6b66d80d899ebc08e7c39e5a2458e/2019-05-06/mountainsort4.simg'
    CONTAINER = 'sha1://8743ff094a26bdedd16f36209a05333f1f82fbd8/2019-06-26/mountainsort4.simg'

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(
        'Use -1, 0, or 1, depending on the sign of the spikes in the recording')
    adjacency_radius = mlpr.FloatParameter(
        'Use -1 to include all channels in every neighborhood')
    freq_min = mlpr.FloatParameter(
        optional=True, default=300, description='Use 0 for no bandpass filtering')
    freq_max = mlpr.FloatParameter(
        optional=True, default=6000, description='Use 0 for no bandpass filtering')
    whiten = mlpr.BoolParameter(optional=True, default=True,
                                description='Whether to do channel whitening as part of preprocessing')
    clip_size = mlpr.IntegerParameter(
        optional=True, default=50, description='')
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=3, description='')
    detect_interval = mlpr.IntegerParameter(
        optional=True, default=10, description='Minimum number of timepoints between events detected on the same channel')
    noise_overlap_threshold = mlpr.FloatParameter(
        optional=True, default=0.15, description='Use None for no automated curation')
    throw_error = mlpr.BoolParameter(optional=True, default=False, description='Intentionally raise an exception for purpose of testing.')

    def run(self):
        if self.throw_error:
            import time
            print('Intentionally throwing an error in 3 seconds (MountainSort4TestError)...')
            sys.stdout.flush()
            time.sleep(3)
            raise Exception('Intentional error.')
        import ml_ms4alg

        print('MountainSort4......')
        recording = SFMdaRecordingExtractor(self.recording_dir)
        num_workers = os.environ.get('NUM_WORKERS', None)
        if num_workers:
            num_workers = int(num_workers)

        # Bandpass filter
        if self.freq_min or self.freq_max:
            recording = bandpass_filter(
                recording=recording, freq_min=self.freq_min, freq_max=self.freq_max)

        # Whiten
        if self.whiten:
            recording = whiten(recording=recording)

        # Sort
        sorting = ml_ms4alg.mountainsort4(
            recording=recording,
            detect_sign=self.detect_sign,
            adjacency_radius=self.adjacency_radius,
            clip_size=self.clip_size,
            detect_threshold=self.detect_threshold,
            detect_interval=self.detect_interval,
            num_workers=num_workers
        )

        # Curate
        # if self.noise_overlap_threshold is not None:
        #    sorting=ml_ms4alg.mountainsort4_curation(
        #      recording=recording,
        #      sorting=sorting,
        #      noise_overlap_threshold=self.noise_overlap_threshold
        #    )

        SFMdaSortingExtractor.write_sorting(
            sorting=sorting, save_path=self.firings_out)

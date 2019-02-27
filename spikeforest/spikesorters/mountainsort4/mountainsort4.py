import mlprocessors as mlpr
import os


class MountainSort4(mlpr.Processor):
    NAME = 'MountainSort4'
    VERSION = '4.2.0'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    CONTAINER = 'sha1://009406add7a55687cec176be912bc7685c2a4b1d/02-12-2019/mountainsort4.simg'
    CONTAINER_SHARE_ID = '69432e9201d0'  # place to look for container

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
        import spikeforest.spikeextractors as se
        import spikeforest.spiketoolkit as st
        import ml_ms4alg

        print('MountainSort4......')
        recording = se.MdaRecordingExtractor(self.recording_dir)
        num_workers = os.environ.get('NUM_WORKERS', None)
        if num_workers:
            num_workers = int(num_workers)

        # Bandpass filter
        if self.freq_min or self.freq_max:
            recording = st.preprocessing.bandpass_filter(
                recording=recording, freq_min=self.freq_min, freq_max=self.freq_max)

        # Whiten
        if self.whiten:
            recording = st.preprocessing.whiten(recording=recording)

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

        se.MdaSortingExtractor.writeSorting(
            sorting=sorting, save_path=self.firings_out)

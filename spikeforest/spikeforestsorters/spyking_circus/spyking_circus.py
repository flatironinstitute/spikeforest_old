import mlprocessors as mlpr
import os
import random
import string
import spikeextractors as se
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor

class SpykingCircus(mlpr.Processor):
    NAME = 'SpykingCircus'
    VERSION = '0.3.3'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS']
    ADDITIONAL_FILES = ['*.params']
    # CONTAINER = 'sha1://8958530b960522d529163344af2faa09ea805716/2019-05-06/spyking_circus.simg'
    # CONTAINER = 'sha1://eed2314fbe2fb1cc7cfe0a36b4e205ffb94add1c/2019-06-17/spyking_circus.simg'
    # CONTAINER = 'sha1://68a175faef53e29af068b8b95649021593f9020a/2019-07-01/spyking_circus.simg'
    CONTAINER = 'sha1://5ca21c482edaf4b3b689f2af3c719a32567ba21e/2019-07-22/spyking_circus.simg'
    LOCAL_MODULES = ['../../spikeforest']

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')

    detect_sign = mlpr.IntegerParameter(description='-1, 1, or 0')
    adjacency_radius = mlpr.FloatParameter(
        optional=True, default=200, description='Channel neighborhood adjacency radius corresponding to geom file')
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=6, description='Threshold for detection')
    template_width_ms = mlpr.FloatParameter(
        optional=True, default=3, description='Spyking circus parameter')
    filter = mlpr.BoolParameter(optional=True, default=True)
    whitening_max_elts = mlpr.IntegerParameter(
        optional=True, default=1000, description='I believe it relates to subsampling and affects compute time')
    clustering_max_elts = mlpr.IntegerParameter(
        optional=True, default=10000, description='I believe it relates to subsampling and affects compute time')

    def run(self):

        import spikesorters as sorters
        print('SpyKING CIRCUS......')
        recording = SFMdaRecordingExtractor(self.recording_dir)
        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/spyking-circus-' + code

        num_workers = int(os.environ.get('NUM_WORKERS', '1'))

        sorter = sorters.SpykingcircusSorter(
            recording=recording,
            output_folder=tmpdir,
            verbose=True,
            delete_output_folder=True
        )

        sorter.set_params(
            detect_sign=self.detect_sign,
            adjacency_radius=self.adjacency_radius,
            detect_threshold=self.detect_threshold,
            template_width_ms=self.template_width_ms,
            filter=self.filter,
            merge_spikes=True,
            auto_merge=0.5,
            num_workers=num_workers,
            electrode_dimensions=None,
            whitening_max_elts=self.whitening_max_elts,
            clustering_max_elts=self.clustering_max_elts,
        )

        # TODO: get elapsed time from the return of this run
        sorter.run()

        sorting = sorter.get_result()

        SFMdaSortingExtractor.write_sorting(
            sorting=sorting, save_path=self.firings_out)

from pathlib import Path

import mlprocessors as mlpr
import spikeextractors as se
from .sfmdaextractors import SFMdaRecordingExtractor, SFMdaSortingExtractor
import os, time, random, string, shutil, sys, shlex, json
from mountaintools import client as mt
from subprocess import Popen, PIPE, CalledProcessError, call


class Tridesclous(mlpr.Processor):
    """
    tridesclous is one of the more convenient, fast and elegant
    spike sorters.

    Installation instruction
        >>> pip install https://github.com/tridesclous/tridesclous/archive/master.zip

    More information on tridesclous at:
    * https://github.com/tridesclous/tridesclous
    * https://tridesclous.readthedocs.io

    """

    NAME = 'Tridesclous'
    VERSION = '0.1.1'  # wrapper VERSION
    ADDITIONAL_FILES = []
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    CONTAINER = 'sha1://9fb4a9350492ee84c8ea5d8692434ecba3cf33da/2019-05-13/tridesclous.simg'
    CONTAINER_SHARE_ID = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')
    channels = mlpr.IntegerListParameter(optional=True, default=[],
                                         description='List of channels to use.')
    detect_sign = mlpr.FloatParameter(optional=True, default=-1, description='')
    detection_threshold = mlpr.FloatParameter(optional=True, default=5.5, description='')
    freq_min = mlpr.FloatParameter(optional=True, default=400, description='')
    freq_max = mlpr.FloatParameter(optional=True, default=5000, description='')
    waveforms_n_left = mlpr.IntegerParameter(description='', optional=True, default=-45)
    waveforms_n_right = mlpr.IntegerParameter(description='', optional=True, default=60)
    align_waveform = mlpr.BoolParameter(description='', optional=True, default=False)
    common_ref_removal = mlpr.BoolParameter(description='', optional=True, default=False)
    peak_span = mlpr.FloatParameter(optional=True, default=.0002, description='')
    alien_value_threshold = mlpr.FloatParameter(optional=True, default=100, description='')

    def run(self):
        import tridesclous as tdc

        tmpdir = Path(_get_tmpdir('tdc'))
        recording = SFMdaRecordingExtractor(self.recording_dir)

        params = {
            'fullchain_kargs': {
                'duration': 300.,
                'preprocessor': {
                    'highpass_freq': self.freq_min,
                    'lowpass_freq': self.freq_max,
                    'smooth_size': 0,
                    'chunksize': 1024,
                    'lostfront_chunksize': 128,
                    'signalpreprocessor_engine': 'numpy',
                    'common_ref_removal': self.common_ref_removal,
                },
                'peak_detector': {
                    'peakdetector_engine': 'numpy',
                    'peak_sign': '-',
                    'relative_threshold': self.detection_threshold,
                    'peak_span': self.peak_span,
                },
                'noise_snippet': {
                    'nb_snippet': 300,
                },
                'extract_waveforms': {
                    'n_left': self.waveforms_n_left,
                    'n_right': self.waveforms_n_right,
                    'mode': 'rand',
                    'nb_max': 20000,
                    'align_waveform': self.align_waveform,
                },
                'clean_waveforms': {
                    'alien_value_threshold': self.alien_value_threshold,
                },
            },
            'feat_method': 'peak_max',
            'feat_kargs': {},
            'clust_method': 'sawchaincut',
            'clust_kargs': {'kde_bandwith': 1.},
        }

        # save prb file:
        probe_file = tmpdir / 'probe.prb'
        se.save_probe_file(recording, probe_file, format='spyking_circus')

        # source file
        if isinstance(recording, se.BinDatRecordingExtractor) and recording._frame_first:
            # no need to copy
            raw_filename = recording._datfile
            dtype = recording._timeseries.dtype.str
            nb_chan = len(recording._channels)
            offset = recording._timeseries.offset
        else:
            # save binary file (chunk by hcunk) into a new file
            raw_filename = tmpdir / 'raw_signals.raw'
            n_chan = recording.get_num_channels()
            chunksize = 2**24 // n_chan
            se.write_binary_dat_format(recording, raw_filename, time_axis=0, dtype='float32', chunksize=chunksize)
            dtype = 'float32'
            offset = 0

        # initialize source and probe file
        tdc_dataio = tdc.DataIO(dirname=str(tmpdir))
        nb_chan = recording.get_num_channels()

        tdc_dataio.set_data_source(type='RawData', filenames=[str(raw_filename)],
                                   dtype=dtype, sample_rate=recording.get_sampling_frequency(),
                                   total_channel=nb_chan, offset=offset)
        tdc_dataio.set_probe_file(str(probe_file))

        try:
            sorting = tdc_helper(tmpdir=tmpdir, params=params, recording=recording)
            SFMdaSortingExtractor.write_sorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                if not getattr(self, '_keep_temp_files', False):
                    shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            shutil.rmtree(tmpdir)


def tdc_helper(
        *,
        tmpdir,
        params,
        recording):

    import tridesclous as tdc

    # nb_chan = recording.get_num_channels()

    # check params and OpenCL when many channels
    use_sparse_template = False
    use_opencl_with_sparse = False
    # if nb_chan > 64:  # this limit depend on the platform of course
    #     if tdc.cltools.HAVE_PYOPENCL:
    #         # force opencl
    #         self.params['fullchain_kargs']['preprocessor']['signalpreprocessor_engine'] = 'opencl'
    #         use_sparse_template = True
    #         use_opencl_with_sparse = True
    #     else:
    #         print('OpenCL is not available processing will be slow, try install it')

    tdc_dataio = tdc.DataIO(dirname=str(tmpdir))
    # make catalogue
    chan_grps = list(tdc_dataio.channel_groups.keys())
    for chan_grp in chan_grps:
        cc = tdc.CatalogueConstructor(dataio=tdc_dataio, chan_grp=chan_grp)
        tdc.apply_all_catalogue_steps(cc, verbose=True, **params)
        cc.make_catalogue_for_peeler()

        # apply Peeler (template matching)
        initial_catalogue = tdc_dataio.load_catalogue(chan_grp=chan_grp)
        peeler = tdc.Peeler(tdc_dataio)
        peeler.change_params(catalogue=initial_catalogue,
                             use_sparse_template=use_sparse_template,
                             sparse_threshold_mad=1.5,
                             use_opencl_with_sparse=use_opencl_with_sparse,)
        peeler.run(duration=None, progressbar=False)

    sorting = se.TridesclousSortingExtractor(tmpdir)
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

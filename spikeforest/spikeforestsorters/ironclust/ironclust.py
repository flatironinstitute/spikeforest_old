import mlprocessors as mlpr
import os
import random
import string
import shutil
from spikeforest import mdaio
import spikeextractors as se
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
from mountaintools import client as mt
import json
import traceback
from typing import Union
from .install_ironclust import install_ironclust


class IronClust(mlpr.Processor):
    NAME = 'IronClust'
    VERSION = '0.5.3'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    CONTAINER: Union[str, None] = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')
    channels = mlpr.IntegerListParameter(
        optional=True, default=[],
        description='List of channels to use.'
    )
    detect_sign = mlpr.IntegerParameter(
        optional=True, default=-1,
        description='Use -1, 0, or 1, depending on the sign of the spikes in the recording'
    )
    adjacency_radius = mlpr.FloatParameter(
        optional=True, default=50,
        description='Use -1 to include all channels in every neighborhood'
    )
    adjacency_radius_out = mlpr.FloatParameter(
        optional=True, default=75,
        description='Use -1 to include all channels in every neighborhood'
    )
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=4.5,
        description='detection threshold'
    )
    prm_template_name = mlpr.StringParameter(
        optional=True, default='',
        description='.prm template file name'
    )
    freq_min = mlpr.FloatParameter(
        optional=True, default=300,
        description='Use 0 for no bandpass filtering'
    )
    freq_max = mlpr.FloatParameter(
        optional=True, default=6000,
        description='Use 0 for no bandpass filtering'
    )
    merge_thresh = mlpr.FloatParameter(
        optional=True, default=0.985,
        description='Threshold for automated merging'
    )
    pc_per_chan = mlpr.IntegerParameter(
        optional=True, default=2,
        description='Number of principal components per channel'
    )

    # added in version 0.2.4
    whiten = mlpr.BoolParameter(
        optional=True, default=False, description='Whether to do channel whitening as part of preprocessing')
    filter_type = mlpr.StringParameter(
        optional=True, default='bandpass', description='{none, bandpass, wiener, fftdiff, ndiff}')
    filter_detect_type = mlpr.StringParameter(
        optional=True, default='none', description='{none, bandpass, wiener, fftdiff, ndiff}')
    common_ref_type = mlpr.StringParameter(
        optional=True, default='none', description='{none, mean, median}')
    batch_sec_drift = mlpr.FloatParameter(
        optional=True, default=300, description='batch duration in seconds. clustering time duration')
    step_sec_drift = mlpr.FloatParameter(
        optional=True, default=20, description='compute anatomical similarity every n sec')
    knn = mlpr.IntegerParameter(
        optional=True, default=30, description='K nearest neighbors')
    min_count = mlpr.IntegerParameter(
        optional=True, default=30, description='Minimum cluster size')
    fGpu = mlpr.BoolParameter(
        optional=True, default=True, description='Use GPU if available')
    fft_thresh = mlpr.FloatParameter(
        optional=True, default=8, description='FFT-based noise peak threshold')
    fft_thresh_low = mlpr.FloatParameter(
        optional=True, default=0, description='FFT-based noise peak lower threshold (set to 0 to disable dual thresholding scheme)')
    nSites_whiten = mlpr.IntegerParameter(
        optional=True, default=32, description='Number of adjacent channels to whiten')        
    feature_type = mlpr.StringParameter(
        optional=True, default='gpca', description='{gpca, pca, vpp, vmin, vminmax, cov, energy, xcov}')
    delta_cut = mlpr.FloatParameter(
        optional=True, default=1, description='Cluster detection threshold (delta-cutoff)')
    post_merge_mode = mlpr.IntegerParameter(
        optional=True, default=1, description='post_merge_mode')
    sort_mode = mlpr.IntegerParameter(
        optional=True, default=1, description='sort_mode')

    @staticmethod
    def install():
        print('Auto-installing ironclust.')
        return install_ironclust(commit='945e3035ff89701ad31a39f930790a1e0894e435')

    def run(self):
        import spikesorters as sorters
        print('IronClust......')

        try:
            ironclust_path = IronClust.install()
        except:
            traceback.print_exc()
            raise Exception('Problem installing ironclust.')
        sorters.IronClustSorter.set_ironclust_path(ironclust_path)


        recording = SFMdaRecordingExtractor(self.recording_dir)
        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/ironclust-' + code

        sorter = sorters.IronClustSorter(
            recording=recording,
            output_folder=tmpdir,
            debug=True,
            delete_output_folder=True
        )

        sorter.set_params(
            detect_sign=self.detect_sign,
            adjacency_radius=self.adjacency_radius,
            adjacency_radius_out=self.adjacency_radius_out,
            detect_threshold=self.detect_threshold,
            prm_template_name=self.prm_template_name,
            freq_min=self.freq_min,
            freq_max=self.freq_max,
            merge_thresh=self.merge_thresh,
            pc_per_chan=self.pc_per_chan,
            whiten=self.whiten,
            filter_type=self.filter_type,
            filter_detect_type=self.filter_detect_type,
            common_ref_type=self.common_ref_type,
            batch_sec_drift=self.batch_sec_drift,
            step_sec_drift=self.step_sec_drift,
            knn=self.knn,
            min_count=self.min_count,
            fGpu=self.fGpu,
            fft_thresh=self.fft_thresh,
            fft_thresh_low=self.fft_thresh_low,
            nSites_whiten=self.nSites_whiten,
            feature_type=self.feature_type,
            delta_cut=self.delta_cut,
            post_merge_mode=self.post_merge_mode,
            sort_mode=self.sort_mode
        )

        # TODO: get elapsed time from the return of this run
        sorter.run()

        sorting = sorter.get_result()

        SFMdaSortingExtractor.write_sorting(
            sorting=sorting, save_path=self.firings_out)


class IronClustOld(mlpr.Processor):
    NAME = 'IronClust'
    VERSION = '0.4.10'
    ENVIRONMENT_VARIABLES = [
        'NUM_WORKERS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'OMP_NUM_THREADS', 'TEMPDIR']
    ADDITIONAL_FILES = ['*.m']
    CONTAINER = None

    recording_dir = mlpr.Input('Directory of recording', directory=True)
    firings_out = mlpr.Output('Output firings file')
    channels = mlpr.IntegerListParameter(
        optional=True, default=[],
        description='List of channels to use.'
    )
    detect_sign = mlpr.IntegerParameter(
        optional=True, default=-1,
        description='Use -1, 0, or 1, depending on the sign of the spikes in the recording'
    )
    adjacency_radius = mlpr.FloatParameter(
        optional=True, default=50,
        description='Use -1 to include all channels in every neighborhood'
    )
    adjacency_radius_out = mlpr.FloatParameter(
        optional=True, default=75,
        description='Use -1 to include all channels in every neighborhood'
    )
    detect_threshold = mlpr.FloatParameter(
        optional=True, default=4.5,
        description='detection threshold'
    )
    prm_template_name = mlpr.StringParameter(
        optional=True, default='',
        description='.prm template file name'
    )
    freq_min = mlpr.FloatParameter(
        optional=True, default=300,
        description='Use 0 for no bandpass filtering'
    )
    freq_max = mlpr.FloatParameter(
        optional=True, default=6000,
        description='Use 0 for no bandpass filtering'
    )
    merge_thresh = mlpr.FloatParameter(
        optional=True, default=0.985,
        description='Threshold for automated merging'
    )
    pc_per_chan = mlpr.IntegerParameter(
        optional=True, default=2,
        description='Number of principal components per channel'
    )

    # added in version 0.2.4
    whiten = mlpr.BoolParameter(
        optional=True, default=False, description='Whether to do channel whitening as part of preprocessing')
    filter_type = mlpr.StringParameter(
        optional=True, default='bandpass', description='{none, bandpass, wiener, fftdiff, ndiff}')
    filter_detect_type = mlpr.StringParameter(
        optional=True, default='none', description='{none, bandpass, wiener, fftdiff, ndiff}')
    common_ref_type = mlpr.StringParameter(
        optional=True, default='none', description='{none, mean, median}')
    batch_sec_drift = mlpr.FloatParameter(
        optional=True, default=300, description='batch duration in seconds. clustering time duration')
    step_sec_drift = mlpr.FloatParameter(
        optional=True, default=20, description='compute anatomical similarity every n sec')
    knn = mlpr.IntegerParameter(
        optional=True, default=30, description='K nearest neighbors')
    min_count = mlpr.IntegerParameter(
        optional=True, default=30, description='Minimum cluster size')
    fGpu = mlpr.BoolParameter(
        optional=True, default=True, description='Use GPU if available')
    fft_thresh = mlpr.FloatParameter(
        optional=True, default=8, description='FFT-based noise peak threshold')
    fft_thresh_low = mlpr.FloatParameter(
        optional=True, default=4, description='FFT-based noise peak lower threshold (set to 0 to disable dual thresholding scheme)')
    nSites_whiten = mlpr.IntegerParameter(
        optional=True, default=32, description='Number of adjacent channels to whiten')        
    feature_type = mlpr.StringParameter(
        optional=True, default='gpca', description='{gpca, pca, vpp, vmin, vminmax, cov, energy, xcov}')
    delta_cut = mlpr.FloatParameter(
        optional=True, default=1.1, description='Cluster detection threshold (delta-cutoff)')
    post_merge_mode = mlpr.IntegerParameter(
        optional=True, default=1, description='post_merge_mode')
    sort_mode = mlpr.IntegerParameter(
        optional=True, default=1, description='sort_mode')

    @staticmethod
    def install():
        print('Auto-installing ironclust.')
        return install_ironclust(commit='82c9b912b5d22d12b9901dc0f5d3c227d405ce79')

    def run(self):
        ironclust_path = os.environ.get('IRONCLUST_PATH_DEV', None)
        if ironclust_path:
            print('Using ironclust from IRONCLUST_PATH_DEV directory: {}'.format(ironclust_path))
        else:
            try:
                ironclust_path = IronClust.install()
            except:
                traceback.print_exc()
                raise Exception('Problem installing ironclust. You can set the IRONCLUST_PATH_DEV to force to use a particular path.')
        print('Using ironclust from: {}'.format(ironclust_path))

        code = ''.join(random.choice(string.ascii_uppercase)
                       for x in range(10))
        tmpdir = os.environ.get('TEMPDIR', '/tmp') + '/ironclust-tmp-' + code

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
            sorting = ironclust_helper(
                recording=recording,
                tmpdir=tmpdir,
                ironclust_path=ironclust_path,
                params=params,
                **all_params)
            SFMdaSortingExtractor.write_sorting(
                sorting=sorting, save_path=self.firings_out)
        except:
            if os.path.exists(tmpdir):
                if not getattr(self, '_keep_temp_files', False):
                    shutil.rmtree(tmpdir)
            raise
        if not getattr(self, '_keep_temp_files', False):
            pass
            # shutil.rmtree(tmpdir)


def ironclust_helper(
        *,
        recording,  # Recording object
        tmpdir,  # Temporary working directory
        params=dict(),
        ironclust_path,
        **kwargs):
    source_dir = os.path.dirname(os.path.realpath(__file__))

    dataset_dir = tmpdir + '/ironclust_dataset'
    # Generate three files in the dataset directory: raw.mda, geom.csv, params.json
    SFMdaRecordingExtractor.write_recording(
        recording=recording, save_path=dataset_dir, params=params, _preserve_dtype=True)

    samplerate = recording.get_sampling_frequency()

    print('Reading timeseries header...')
    HH = mdaio.readmda_header(dataset_dir + '/raw.mda')
    num_channels = HH.dims[0]
    num_timepoints = HH.dims[1]
    duration_minutes = num_timepoints / samplerate / 60
    print('Num. channels = {}, Num. timepoints = {}, duration = {} minutes'.format(
        num_channels, num_timepoints, duration_minutes))

    print('Creating argfile.txt...')
    txt = ''
    for key0, val0 in kwargs.items():
        txt += '{}={}\n'.format(key0, val0)
    txt += 'samplerate={}\n'.format(samplerate)
    if 'scale_factor' in params:
        txt += 'scale_factor={}\n'.format(params["scale_factor"])
    _write_text_file(dataset_dir + '/argfile.txt', txt)

    # new method
    print('Running ironclust in {tmpdir}...'.format(tmpdir=tmpdir))
    cmd = '''
        addpath('{source_dir}');
        addpath('{ironclust_path}', '{ironclust_path}/matlab', '{ironclust_path}/matlab/mdaio');
        try
            p_ironclust('{tmpdir}', '{dataset_dir}/raw.mda', '{dataset_dir}/geom.csv', '', '', '{tmpdir}/firings.mda', '{dataset_dir}/argfile.txt');
        catch
            fprintf('----------------------------------------');
            fprintf(lasterr());
            quit(1);
        end
        quit(0);
    '''
    cmd = cmd.format(ironclust_path=ironclust_path, tmpdir=tmpdir, dataset_dir=dataset_dir, source_dir=source_dir)

    matlab_cmd = mlpr.ShellScript(cmd, script_path=tmpdir + '/run_ironclust.m', keep_temp_files=True)
    matlab_cmd.write()

    shell_cmd = '''
        #!/bin/bash
        cd {tmpdir}
        matlab -nosplash -nodisplay -r run_ironclust
    '''.format(tmpdir=tmpdir)
    shell_cmd = mlpr.ShellScript(shell_cmd, script_path=tmpdir + '/run_ironclust.sh', keep_temp_files=True)
    shell_cmd.write(tmpdir + '/run_ironclust.sh')
    shell_cmd.start()

    retcode = shell_cmd.wait()

    if retcode != 0:
        raise Exception('ironclust returned a non-zero exit code')

    # parse output
    result_fname = tmpdir + '/firings.mda'
    if not os.path.exists(result_fname):
        raise Exception('Result file does not exist: ' + result_fname)

    firings = mdaio.readmda(result_fname)
    sorting = se.NumpySortingExtractor()
    sorting.set_times_labels(firings[1, :], firings[2, :])
    return sorting


def _read_text_file(fname):
    with open(fname) as f:
        return f.read()


def _write_text_file(fname, str):
    with open(fname, 'w') as f:
        f.write(str)


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

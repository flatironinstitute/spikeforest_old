from spikeextractors import RecordingExtractor
from spikeextractors import SortingExtractor

import json
import numpy as np
from .mdaio import DiskReadMda, readmda, writemda32, writemda64
import os
import mtlogging
import mlprocessors as mlpr

def _load_required_modules():
    try:
        from mountaintools import client as mt
    except ModuleNotFoundError:
        raise ModuleNotFoundError("To use the MdaExtractors, install mountainlab_pytools and kbucket: \n\n"
                                  "pip install mountainlab_pytools kbucket\n\n")
    return mt


class SFMdaRecordingExtractor(RecordingExtractor):
    def __init__(self, dataset_directory, *, download=True, raw_fname='raw.mda', params_fname='params.json'):
        ca = _load_required_modules()

        RecordingExtractor.__init__(self)
        self._dataset_directory = dataset_directory
        self._timeseries_path = dataset_directory + '/' + raw_fname
        self._dataset_params = read_dataset_params(dataset_directory, params_fname)
        self._samplerate = self._dataset_params['samplerate'] * 1.0
        if download:
            path0 = ca.realizeFile(path=self._timeseries_path)
            if not path0:
                raise Exception('Unable to realize file: ' + self._timeseries_path)
            self._timeseries_path = path0

        
        geom0 = dataset_directory + '/geom.csv'
        self._geom_fname = ca.realizeFile(path=geom0)
        self._geom = np.genfromtxt(self._geom_fname, delimiter=',')

        timeseries_path_or_url = self._timeseries_path
        if not ca.isLocalPath(timeseries_path_or_url):
            a = ca.findFile(timeseries_path_or_url)
            if not a:
                raise Exception('Cannot find timeseries file: '+timeseries_path_or_url)
            timeseries_path_or_url = a

        # if is_kbucket_url(timeseries0):
        #     download_needed = is_url(ca.findFile(path=timeseries0))
        # else:
        #     download_needed = is_url(timeseries0)
        # if download and download_needed:
        #     print('Downloading file: ' + timeseries0)
        #     self._timeseries_path = ca.realizeFile(path=timeseries0)
        #     print('Done.')
        # else:
        #     self._timeseries_path = ca.findFile(path=timeseries0)

        X = DiskReadMda(timeseries_path_or_url)
        if self._geom.shape[0] != X.N1():
            #raise Exception(
            #    'Incompatible dimensions between geom.csv and timeseries file {} <> {}'.format(self._geom.shape[0], X.N1()))
            print('WARNING: Incompatible dimensions between geom.csv and timeseries file {} <> {}'.format(self._geom.shape[0], X.N1()))
            self._geom=np.zeros((X.N1(), 2))

        self._num_channels = X.N1()
        self._num_timepoints = X.N2()
        for m in range(self._num_channels):
            self.setChannelProperty(m, 'location', self._geom[m, :])

    def hash(self):
        from mountainclient import client as mt
        obj = dict(
            raw = mt.computeFileSha1(self._timeseries_path),
            geom = mt.computeFileSha1(self._geom_fname),
            params = self._dataset_params
        )
        return mt.sha1OfObject(obj)

    def recordingDirectory(self):
        return self._dataset_directory

    def getChannelIds(self):
        return list(range(self._num_channels))

    def getNumFrames(self):
        return self._num_timepoints

    def getSamplingFrequency(self):
        return self._samplerate

    @mtlogging.log(name='SFMdaRecordingExtractor:getTraces')
    def getTraces(self, channel_ids=None, start_frame=None, end_frame=None):
        ca = _load_required_modules()
        if not ca.isLocalPath(self._timeseries_path):
            raise Exception('Cannot get traces -- timeseries file is not downloaded')
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = self.getNumFrames()
        if channel_ids is None:
            channel_ids = self.getChannelIds()
        X = DiskReadMda(self._timeseries_path)
        recordings = X.readChunk(i1=0, i2=start_frame, N1=X.N1(), N2=end_frame - start_frame)
        recordings = recordings[channel_ids, :]
        return recordings

    @staticmethod
    def writeRecording(recording, save_path, params=dict(), raw_fname='raw.mda', params_fname='params.json'):
        # ca = _load_required_modules()
        channel_ids = recording.getChannelIds()
        M = len(channel_ids)
        # N = recording.getNumFrames()
        raw = recording.getTraces()
        location0 = recording.getChannelProperty(channel_ids[0], 'location')
        nd = len(location0)
        geom = np.zeros((M, nd))
        for ii in range(len(channel_ids)):
            location_ii = recording.getChannelProperty(channel_ids[ii], 'location')
            geom[ii, :] = list(location_ii)
        if not os.path.isdir(save_path):
            os.mkdir(save_path)
        writemda32(raw, save_path + '/' + raw_fname)
        params["samplerate"] = recording.getSamplingFrequency()
        with open(save_path + '/' + params_fname,'w') as f:
            json.dump(params, f)
        np.savetxt(save_path + '/geom.csv', geom, delimiter=',')

class SFMdaSortingExtractor(SortingExtractor):
    def __init__(self, firings_file):
        ca = _load_required_modules()

        SortingExtractor.__init__(self)
        if is_kbucket_url(firings_file):
            download_needed = is_url(ca.findFile(path=firings_file))
        else:
            download_needed = is_url(firings_file)
        if download_needed:
            print('Downloading file: ' + firings_file)
            self._firings_path = ca.realizeFile(path=firings_file)
            print('Done.')
        else:
            self._firings_path = ca.realizeFile(path=firings_file)
        if not self._firings_path:
            raise Exception('Unable to realize firings file: '+firings_file)
        
        self._firings = readmda(self._firings_path)
        self._times = self._firings[1, :]
        self._labels = self._firings[2, :]
        self._unit_ids = np.unique(self._labels).astype(int)

    def getUnitIds(self):
        return self._unit_ids

    def getUnitSpikeTrain(self, unit_id, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = np.Inf
        inds = np.where((self._labels == unit_id) & (start_frame <= self._times) & (self._times < end_frame))
        return np.rint(self._times[inds]).astype(int)

    def hash(self):
        from mountaintools import client as mt
        return mt.computeFileSha1(self._firings_path)

    @staticmethod
    def writeSorting(sorting, save_path):
        # ca = _load_required_modules()
        unit_ids = sorting.getUnitIds()
        # if len(unit_ids) > 0:
        #     K = np.max(unit_ids)
        # else:
        #     K = 0
        times_list = []
        labels_list = []
        for i in range(len(unit_ids)):
            unit = unit_ids[i]
            times = sorting.getUnitSpikeTrain(unit_id=unit)
            times_list.append(times)
            labels_list.append(np.ones(times.shape) * unit)
        all_times = _concatenate(times_list)
        all_labels = _concatenate(labels_list)
        sort_inds = np.argsort(all_times)
        all_times = all_times[sort_inds]
        all_labels = all_labels[sort_inds]
        L = len(all_times)
        firings = np.zeros((3, L))
        firings[1, :] = all_times
        firings[2, :] = all_labels
        writemda64(firings, save_path)


def _concatenate(list):
    if len(list) == 0:
        return np.array([])
    return np.concatenate(list)


def is_kbucket_url(path):
    path = path or ''
    return path.startswith('kbucket://') or path.startswith('sha1://') or path.startswith('sha1dir://')


def is_url(path):
    path = path or ''
    return path.startswith('http://') or path.startswith('https://') or path.startswith(
        'kbucket://') or path.startswith('sha1://') or path.startswith('sha1dir://')


def read_dataset_params(dsdir, params_fname):
    ca = _load_required_modules()

    fname1=dsdir+'/'+params_fname
    fname2=ca.realizeFile(path=fname1)
    if not fname2:
        raise Exception('Unable to find file: '+fname1)
    if not os.path.exists(fname2):
        raise Exception('Dataset parameter file does not exist: ' + fname2)
    with open(fname2) as f:
        return json.load(f)

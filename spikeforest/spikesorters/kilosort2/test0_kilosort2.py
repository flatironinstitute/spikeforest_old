import os
import sys

# def append_to_path(dir0): # A convenience function
#     if dir0 not in sys.path:
#         sys.path.append(dir0)
# append_to_path(os.getcwd()+'/..')
from spikesorters import KiloSort2
from spikeforest import example_datasets
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
import tempfile
import shutil
from mountaintools import client as mt
import pytest


def setup_module(module):
    # Use this so we can download containers as needed
    mt.configDownloadFrom(['spikeforest.spikeforest2'])

    # Check if singularity is installed
    retval = os.system('singularity --version')
    assert retval == 0, 'Singularity is not installed'


def teardown_module(module):
    pass


def setup_function(function):
    pass


def teardown_function(function):
    pass


@pytest.mark.kilosort2
def test_kilosort2(tmpdir):
    tmpdir = str(tmpdir)

    #rx, sx = example_datasets.toy_example1()
    rx = SFMdaRecordingExtractor('/mnt/home/jjun/ceph/groundtruth/hybrid_drift/rec_64c_1200s_11')
    sx = SFMdaSortingExtractor('/mnt/home/jjun/ceph/groundtruth/hybrid_drift/rec_64c_1200s_11/firings_true.mda')

    SFMdaRecordingExtractor.writeRecording(
        recording=rx, save_path=tmpdir+'/recording')
    SFMdaSortingExtractor.writeSorting(
        sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')

    KiloSort2.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default',
        _keep_temp_files=True,
        _force_run=True
    )
    assert os.path.exists(tmpdir+'/firings.mda')

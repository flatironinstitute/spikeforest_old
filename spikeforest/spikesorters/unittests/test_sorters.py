import os
import sys

# def append_to_path(dir0): # A convenience function
#     if dir0 not in sys.path:
#         sys.path.append(dir0)
# append_to_path(os.getcwd()+'/..')
from spikesorters import MountainSort4, SpykingCircus, YASS, KiloSort, IronClust
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


@pytest.mark.slow
@pytest.mark.mountainsort4
def test_mountainsort4(tmpdir):
    tmpdir = str(tmpdir)

    rx, sx = example_datasets.toy_example1()
    SFMdaRecordingExtractor.writeRecording(
        recording=rx, save_path=tmpdir+'/recording')
    SFMdaSortingExtractor.writeSorting(
        sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')

    MountainSort4.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default'
    )
    assert os.path.exists(tmpdir+'/firings.mda')


@pytest.mark.slow
@pytest.mark.spyking_circus
def test_spyking_circus(tmpdir):
    tmpdir = str(tmpdir)

    rx, sx = example_datasets.toy_example1()
    SFMdaRecordingExtractor.writeRecording(
        recording=rx, save_path=tmpdir+'/recording')
    SFMdaSortingExtractor.writeSorting(
        sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')

    SpykingCircus.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default'
    )
    assert os.path.exists(tmpdir+'/firings.mda')


@pytest.mark.slow
@pytest.mark.yass
def test_yass(tmpdir):
    tmpdir = str(tmpdir)

    rx, sx = example_datasets.toy_example1()
    SFMdaRecordingExtractor.writeRecording(
        recording=rx, save_path=tmpdir+'/recording')
    SFMdaSortingExtractor.writeSorting(
        sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')

    YASS.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default'
    )
    assert os.path.exists(tmpdir+'/firings.mda')


@pytest.mark.exclude
@pytest.mark.kilosort
def test_kilosort(tmpdir):
    tmpdir = str(tmpdir)

    rx, sx = example_datasets.toy_example1()
    SFMdaRecordingExtractor.writeRecording(
        recording=rx, save_path=tmpdir+'/recording')
    SFMdaSortingExtractor.writeSorting(
        sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')

    KiloSort.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default'
    )
    assert os.path.exists(tmpdir+'/firings.mda')

@pytest.mark.exclude
@pytest.mark.ironclust
def test_ironclust(tmpdir):
    tmpdir = str(tmpdir)

    rx, sx = example_datasets.toy_example1()
    SFMdaRecordingExtractor.writeRecording(
        recording=rx, save_path=tmpdir+'/recording')
    SFMdaSortingExtractor.writeSorting(
        sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')

    IronClust.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default'
    )
    assert os.path.exists(tmpdir+'/firings.mda')

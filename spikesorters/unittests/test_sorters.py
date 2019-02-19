import os, sys

# def append_to_path(dir0): # A convenience function
#     if dir0 not in sys.path:
#         sys.path.append(dir0)
# append_to_path(os.getcwd()+'/..')
from spikesorters import MountainSort4, SpykingCircus, YASS
import spikeextractors as se
import tempfile
import shutil
from cairio import client as ca

def setup_module(module):
    # Use this so we can download containers as needed
    ca.setRemoteConfig(alternate_share_ids=['69432e9201d0'])
 
def teardown_module(module):
    pass

def setup_function(function):
    pass
 
def teardown_function(function):
    pass

def test_mountainsort4(tmpdir):
    tmpdir=str(tmpdir)

    rx, sx = se.example_datasets.toy_example1()
    se.MdaRecordingExtractor.writeRecording(recording=rx,save_path=tmpdir+'/recording')
    se.MdaSortingExtractor.writeSorting(sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')
    
    MountainSort4.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default'
    )
    assert os.path.exists(tmpdir+'/firings.mda')

def test_spyking_circus(tmpdir):
    tmpdir=str(tmpdir)

    rx, sx = se.example_datasets.toy_example1()
    se.MdaRecordingExtractor.writeRecording(recording=rx,save_path=tmpdir+'/recording')
    se.MdaSortingExtractor.writeSorting(sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')
    
    SpykingCircus.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default'
    )
    assert os.path.exists(tmpdir+'/firings.mda')

def test_yass(tmpdir):
    tmpdir=str(tmpdir)

    rx, sx = se.example_datasets.toy_example1()
    se.MdaRecordingExtractor.writeRecording(recording=rx,save_path=tmpdir+'/recording')
    se.MdaSortingExtractor.writeSorting(sorting=sx, save_path=tmpdir+'/recording/firings_true.mda')
    
    YASS.execute(
        recording_dir=tmpdir+'/recording',
        firings_out=tmpdir+'/firings.mda',
        detect_sign=-1,
        adjacency_radius=50,
        _container='default'
    )
    assert os.path.exists(tmpdir+'/firings.mda')

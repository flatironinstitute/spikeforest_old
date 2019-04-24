import sys
from mountaintools import client as mt
from .core import ForestViewMainWindow
from .spikeforestcontext import SpikeForestContext
from .analysiscontext import AnalysisContext
import os

def forestview(path, *, mode='spikeforest'):
    if mode == 'spikeforest':
        context = _load_spikeforest_context(path)
    elif mode == 'analysis':
        context = _load_analysis_context(path)
    else:
        raise Exception('Invalid mode: '+mode)

    if not context:
        raise Exception('Unable to create context.')

    W = ForestViewMainWindow(context=context)

    return W

def _load_spikeforest_context(path):
    if mt.isFile(path):
        obj = mt.loadObject(path=path)
        if not obj:
            print('Unable to load file: '+path, file=sys.stderr)
            return None
    else:
        obj = _make_obj_from_dir(path)
        if not obj:
            print('Unable to make object from path: '+path)
            return None
    context = SpikeForestContext(
        studies = obj.get('studies', []),
        recordings = obj.get('recordings', []),
        sorting_results = obj.get('sorting_results', []),
        aggregated_sorting_results = obj.get('aggregated_sorting_results', None)
    )
    return context

def _load_analysis_context(path):
    obj = mt.loadObject(path=path)
    if not obj:
        print('Unable to load file: '+path, file=sys.stderr)
        return None
    context = AnalysisContext(
        obj = obj
    )
    return context

def _make_obj_from_dir(path):
    studies = []
    recordings = []
    study_name = os.path.basename(path)
    studies.append(dict(
        name=study_name,
        description='Loaded from '+path
    ))
    dd = mt.readDir(path)
    if not dd:
        print('Unable to read directory: '+path)
        return None
    if 'raw.mda' in dd['files']:
        recordings.append(_make_recording_obj_from_dir(
            path=path,
            study_name=study_name,
            name='recording'
        ))
    else:
        for dname in dd['dirs'].keys():
            recordings.append(_make_recording_obj_from_dir(
                path=path+'/'+dname,
                study_name=study_name,
                name=dname
            ))
    return dict(
        studies=studies,
        recordings=recordings
    )

def _make_recording_obj_from_dir(*, path, study_name, name):
    ret = dict(
        study=study_name,
        name=name,
        directory=path
    )
    if mt.computeFileSha1(path+'/firings_true.mda'):
        ret['firings_true']=path+'/firings_true.mda'
    intra_raw_fname = path+'/raw_true.mda'
    if mt.computeFileSha1(intra_raw_fname):
        ret['intra_recording']=dict(
            study=study_name,
            name=name+'--intra',
            directory=path,
            raw_fname='raw_true.mda',
            params_fname='params_true.json'
        )
    return ret
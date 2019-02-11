from cairio import client as ca
from PIL import Image
import json
import pandas as pd
import spikeextractors as si

def kb_read_text_file(fname):
    return ca.loadText(path=fname)
    
def kb_read_json_file(fname):
    return ca.loadObject(path=fname)

class SFSortingResult():
    def __init__(self,obj,recording):
        self._obj=obj
        self._recording=recording
    def getObject(self):
        return self._obj
    def recording(self):
        return self._recording
    def sorterName(self):
        return self._obj['sorter_name']
    def plotNames(self):
        plots=self._obj['summary'].get('plots',dict())
        return list(plots.keys())
    def sorting(self):
        return si.MdaSortingExtractor(firings_file=self._obj['firings'])
    def plot(self,name,format='image'):
        plots=self._obj['summary'].get('plots',dict())
        url=plots[name]
        if format=='url':
            return url
        else:
            path=ca.realizeFile(url)
            if format=='image':
                return Image.open(path)
            elif format=='path':
                return path
            else:
                raise Exception('Invalid format: '+format)
    def comparisonWithTruth(self,*,format='dataframe'):
        A=self._obj['comparison_with_truth']
        if format=='html':
            return kb_read_text_file(A['html'])
        else:
            B=kb_read_json_file(A['json'])
            if format=='json':
                return B
            elif format=='dataframe':
                return pd.DataFrame(B).transpose()
            else:
                raise Exception('Invalid format: '+format)

class SFRecording():
    def __init__(self,obj,study):
        self._obj=obj
        self._sorting_result_names=[]
        self._sorting_results_by_name=dict()
        self._summary_result=None
        if 'summary' in obj:
            self._summary_result=obj['summary']
        self._study=study
    def getObject(self):
        return self._obj
    def getSummaryObject(self):
        return self._summary_result
    def study(self):
        return self._study
    def name(self):
        return self._obj['name']
    def description(self):
        return self._obj['description']
    def directory(self):
        return self._obj['directory']
    def recordingFileIsLocal(self):
        fname=self.directory()+'/raw.mda'
        fname2=ca.findFile(fname, local_only=True)
        if fname2 and (not _is_url(fname2)):
            return True
        return False
    def realizeRecordingFile(self):
        fname=self.directory()+'/raw.mda'
        return ca.realizeFile(fname)
    def firingsTrueFileIsLocal(self):
        fname=self.directory()+'/firings_true.mda'
        fname2=ca.findFile(fname, local_only=True)
        if fname2 and (not _is_url(fname2)):
            return True
        return False
    def realizeFiringsTrueFile(self):
        fname=self.directory()+'/firings_true.mda'
        return ca.realizeFile(fname)
    def recordingExtractor(self,download=False):
        X=si.MdaRecordingExtractor(dataset_directory=self.directory(),download=download)
        if 'channels' in self._obj:
            if self._obj['channels']:
                X=si.SubRecordingExtractor(parent_recording=X,channel_ids=self._obj['channels'])
        return X
    def sortingTrue(self):
        return si.MdaSortingExtractor(firings_file=self.directory()+'/firings_true.mda')
    def plotNames(self):
        if not self._summary_result:
            return []
        plots=self._summary_result.get('plots',dict())
        return list(plots.keys())
    def plot(self,name,format='image'):
        plots=self._summary_result.get('plots',dict())
        url=plots[name]
        if format=='url':
            return url
        else:
            path=ca.realizeFile(url)
            if format=='image':
                return Image.open(path)
            elif format=='path':
                return path
            else:
                raise Exception('Invalid format: '+format)
    def trueUnitsInfo(self,format='dataframe'):
        if not self._summary_result:
            return None
        B=kb_read_json_file(self._summary_result['true_units_info'])
        if format=='json':
            return B
        elif format=='dataframe':
            return pd.DataFrame(B)
        else:
            raise Exception('Invalid format: '+format)
    def setSummaryResult(self,obj):
        self._summary_result=obj
    def addSortingResult(self,obj):
        sorter_name=obj['sorter_name']
        if sorter_name in self._sorting_results_by_name:
            print ('Sorting result already in recording: {}'.format(sorter_name))
        else:
            R=SFSortingResult(obj,self)
            self._sorting_result_names.append(sorter_name)
            self._sorting_results_by_name[sorter_name]=R
    def sortingResultNames(self):
        return self._sorting_result_names
    def sortingResult(self,name):
        return self._sorting_results_by_name.get(name,None)

class SFStudy():
    def __init__(self,obj):
        self._obj=obj
        self._recordings_by_name=dict()
        self._recording_names=[]
    def getObject(self):
        return self._obj
    def name(self):
        return self._obj['name']
    def description(self):
        return self._obj['description']
    def addRecording(self,obj):
        name=obj['name']
        if name in self._recordings_by_name:
            print ('Recording already in study: '+name)
        else:
            self._recording_names.append(name)
            D=SFRecording(obj,self)
            self._recordings_by_name[name]=D
    def recordingNames(self):
        return self._recording_names
    def recording(self,name):
        return self._recordings_by_name.get(name,None)
        

class SFData():
    def __init__(self):
        self._studies_by_name=dict()
        self._study_names=[]
    def loadStudy(self,study):
        name=study['name']
        if name in self._studies_by_name:
            print ('Study already loaded: '+name)
        else:
            self._study_names.append(study['name'])
            S=SFStudy(study)
            self._studies_by_name[name]=S
    def loadStudies(self,studies):
        for study in studies:
            self.loadStudy(study)
    def loadRecording(self,recording):
        study=recording['study']
        self._studies_by_name[study].addRecording(recording)
    def loadRecordings2(self,recordings):
        for recording in recordings:
            self.loadRecording(recording)
    def loadRecordings(self,*,key=None,verbose=False):
        # old
        if key is None:
            key=dict(name='spikeforest_studies_processed')
        obj=ca.loadObject(key=key)
        studies=obj['studies']
        for study in studies:
            name=study['name']
            if name in self._studies_by_name:
                print ('Study already loaded: '+name)
            else:
                self._study_names.append(study['name'])
                S=SFStudy(study)
                self._studies_by_name[name]=S
        recordings=obj['recordings']
        print('recordings ===================================================================')
        print(recordings)
        for ds in recordings:
            study=ds['study']
            self._studies_by_name[study].addRecording(ds)
        if verbose:
            print ('Loaded {} recordings'.format(len(recordings)))
    def loadSortingResults(self,sorting_results):
        for result in sorting_results:
            self.loadSortingResult(result)
    def loadSortingResult(self,X):
        study_name=X['recording']['study']
        recording_name=X['recording']['name']
        sorter_name=X['sorter']['name']
        sorting=X['sorting']
        S=self.study(study_name)
        if S:
            D=S.recording(recording_name)
            if D:
                D.addSortingResult(sorting)
            else:
                print ('Warning: recording not found: '+recording_name)
        else:
            print ('Warning: study not found: '+study_name)
    def loadProcessingBatch(self,*,batch_name=None,key=None,verbose=False):
        if batch_name:
            key=dict(name='batcho_batch_results',batch_name=batch_name)
        if not pa.get(key=key):
            raise Exception('Batch result not found.')
        obj=ca.loadObject(key=key)
        job_results=obj.get('job_results',obj.get('results')) # transitioning to 'results'
        num_sorting_results=0
        num_recording_summary_results=0
        for X in job_results:
            if X['job']['command']=='sort_recording':
                study_name=X['job']['recording']['study']
                recording_name=X['job']['recording']['name']
                sorter_name=X['job']['sorter']['name']
                result=X['result']
                S=self.study(study_name)
                if S:
                    D=S.recording(recording_name)
                    if D:
                        num_sorting_results=num_sorting_results+1
                        D.addSortingResult(result)
                    else:
                        print ('Warning: recording not found: '+recording_name)
                else:
                    print ('Warning: study not found: '+study_name)
            elif X['job']['command']=='summarize_recording':
                study_name=X['job']['recording']['study']
                recording_name=X['job']['recording']['name']
                result=X['result']
                S=self.study(study_name)
                if S:
                    D=S.recording(recording_name)
                    if D:
                        num_recording_summary_results=num_recording_summary_results+1
                        D.setSummaryResult(result)
                    else:
                        print ('Warning: recording not found: '+recording_name)
                else:
                    print ('Warning: study not found: '+study_name)
            else:
                pass
        if verbose:
            print ('Loaded {} sorting results and {} recording summary results'.format(num_sorting_results,num_recording_summary_results))

    def studyNames(self):
        return self._study_names
    def study(self,name):
        return self._studies_by_name.get(name,None)

def _is_url(path):
    return (path.startswith('http://') or path.startswith('https://'))
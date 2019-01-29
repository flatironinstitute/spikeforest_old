import vdomr as vd
import spikeforest as sf
from kbucket import client as kb
import pandas as pd
import numpy as np

class SFBrowser(vd.Component):
  def __init__(self,group):
    vd.Component.__init__(self)

    self._group=group
    SF=sf.SFData()
    a=kb.loadObject(key=dict(name='spikeforest_batch_group',group_name=group))
    for recordings_name in a['recordings_names']:
        try:
            SF.loadRecordings(key=dict(name=recordings_name))
        except:
            raise
            print('Warning: unable to load recordings: '+recordings_name)
        for batch_name in a['batch_names']:
            try:
                SF.loadProcessingBatch(batch_name=batch_name)
            except:
                print('Warning: unable to load processing batch: '+batch_name)
    self._SF_data=SF
    self._accuracy_threshold_input=vd.components.LineEdit(value=0.8,dtype=float,style=dict(width='70px'))
    self._update_button=vd.components.Button(onclick=self._on_update,class_='button',label='Update')

    vd.devel.loadBootstrap()

    self._update_accuracy_table()

  def _on_update(self):
      print('_on_update')
      self._update_accuracy_table()

  def _update_accuracy_table(self):
    accuracy_threshold=self._accuracy_threshold_input.value()
    self._accuracy_table, self._sorters=_get_accuracy_table(self._SF_data,accuracy_threshold=accuracy_threshold)
    self.refresh()
    
  def render(self):
    SF=self._SF_data

    table=_to_table(self._accuracy_table,['study']+self._sorters)
    return vd.div(
        vd.table(
            vd.tr(
                vd.td('Accuracy threshold:'),
                vd.td(self._accuracy_threshold_input),
                vd.td(self._update_button)
            ),
            class_='table',
            style={'max-width':'200px'}
        ),
        table,
        style=dict(padding='15px')
    )

def _to_table(X,column_names):
    rows=[]
    rows.append(vd.tr([vd.th(cname) for cname in column_names]))
    for x in X:
        rows.append(vd.tr([vd.td(str(x.get(cname))) for cname in column_names]))
    return vd.table(rows,class_='table')

def _get_study_sorting_results(study):
  results=[]
  for rname in study.recordingNames():
    rec=study.recording(rname)
    true_units_info=rec.trueUnitsInfo(format='json')
    true_units_info_by_id=dict()
    for true_unit in true_units_info:
      true_units_info_by_id[true_unit['unit_id']]=true_unit
    for srname in rec.sortingResultNames():
      a=rec.sortingResult(srname)
      res0=dict(sorter=srname,recording=rname,study=study.name())
      tmp=a.comparisonWithTruth(format='json')
      for i in tmp:
        tmp[i]['true_unit_info']=true_units_info_by_id[tmp[i]['unit_id']]
      res0['comparison_with_truth']=tmp
      results.append(res0)
      
  sorters=list(set([a['sorter'] for a in results]))
  sorters.sort()
  
  units_by_sorter=dict()
  for sorter in sorters:
    units_by_sorter[sorter]=[]
    
  for obj in results:
    sorter0=obj['sorter']
    units=[obj['comparison_with_truth'][i] for i in obj['comparison_with_truth']]
    units_by_sorter[sorter0]=units_by_sorter[sorter0]+units
    
  ret=dict()
  for sorter in sorters:
    units=units_by_sorter[sorter]
    try:
        ret[sorter]=dict(
            true_unit_ids=[unit['unit_id'] for unit in units],
            true_unit_snrs=np.array([unit['true_unit_info']['snr'] for unit in units]),
            true_unit_firing_rates=np.array([unit['true_unit_info']['firing_rate'] for unit in units]),
            num_matches=np.array([unit['num_matches'] for unit in units]),
            num_false_positives=np.array([unit['num_false_positives'] for unit in units]),
            num_false_negatives=np.array([unit['num_false_negatives'] for unit in units])
        )
    except:
        print('WARNING: Problem loading results for sorter: '+sorter)
        ret[sorter]=dict(
            true_unit_ids=[],
            true_unit_snrs=np.array([]),
            true_unit_firing_rates=np.array([]),
            num_matches=np.array([]),
            num_false_positives=np.array([]),
            num_false_negatives=np.array([])
        )
    
  return ret
      
def _get_accuracy_table(SF_data,*,accuracy_threshold):
    SF=SF_data
    accuracy_table=[]
    sorters=set()
    for sname in SF.studyNames():
        print(sname)
        study=SF.study(sname)
        b=_get_study_sorting_results(study)
        tmp=dict(study=sname)
        for sorter in b:
            sorters.add(sorter)
            a=b[sorter]
            accuracies=a['num_matches']/(a['num_matches']+a['num_false_positives']+a['num_false_negatives'])
            tmp[sorter]=np.count_nonzero(accuracies>=accuracy_threshold)
        accuracy_table.append(tmp)
    
    sorters=list(sorters)
    sorters.sort()
    return accuracy_table, sorters
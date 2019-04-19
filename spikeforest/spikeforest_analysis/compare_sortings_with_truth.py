#from spikeforest import spikewidgets as sw
import mlprocessors as mlpr
import json
from mountaintools import client as mt
import numpy as np
from copy import deepcopy
import multiprocessing
import mtlogging

import spikeextractors as si
from spikeforest import SFMdaRecordingExtractor, SFMdaSortingExtractor
from .sortingcomparison import SortingComparison

def _create_job_for_sorting_helper(kwargs):
    return _create_job_for_sorting(**kwargs)

def _create_job_for_sorting(sorting, container):
    if sorting['firings'] is None:
        from mlprocessors import MountainJob
        return MountainJob()
    units_true=sorting.get('units_true',[])
    firings=sorting['firings']
    firings_true=sorting['firings_true']
    units_true=units_true
    job=GenSortingComparisonTable.createJob(
        firings=firings,
        firings_true=firings_true,
        units_true=units_true,
        json_out={'ext':'.json','upload':True},
        html_out={'ext':'.html','upload':True},
        _container=container
    )
    return job

@mtlogging.log()
def compare_sortings_with_truth(sortings,compute_resource,num_workers=None,label=None):
    print('')
    print('>>>>>> {}'.format(label or 'compare sortings with truth'))
    container='sha1://1ad2478736ad188ab5050289ffb1d2c29d1ba750/03-29-2019/spikeforest_basic.simg'

    sortings_out = deepcopy(sortings)
    sortings_valid = [sorting for sorting in sortings_out if (sorting['firings'] is not None)]
    jobs_gen_table = GenSortingComparisonTable.createJobs([
        dict(
            firings=sorting['firings'],
            firings_true=sorting['firings_true'],
            units_true=sorting.get('units_true', []),
            json_out={'ext':'.json','upload':True},
            html_out={'ext':'.html','upload':True},
            _container=container
        )
        for sorting in sortings_valid
    ])

    # jobs_gen_table=[]
    # for sorting in sortings:
    #     units_true=sorting.get('units_true',[])
    #     firings=sorting['firings']
    #     firings_true=sorting['firings_true']
    #     units_true=units_true
    #     job=GenSortingComparisonTable.createJob(
    #         firings=firings,
    #         firings_true=firings_true,
    #         units_true=units_true,
    #         json_out={'ext':'.json','upload':True},
    #         html_out={'ext':'.html','upload':True},
    #         _container=container
    #     )
    #     jobs_gen_table.append(job)
    
    label=label or 'Compare sortings with truth'
    mlpr.executeBatch(jobs=jobs_gen_table,label=label,num_workers=num_workers,compute_resource=compute_resource)

    for sorting in sortings_out:
        sorting['comparison_with_truth'] = None

    for ii, sorting in enumerate(sortings_valid):
        comparison_with_truth = dict()
        comparison_with_truth['json'] = jobs_gen_table[ii].result.outputs['json_out']
        comparison_with_truth['html'] = jobs_gen_table[ii].result.outputs['html_out']
        sorting['comparison_with_truth'] = comparison_with_truth

    return sortings_out

class GenSortingComparisonTable(mlpr.Processor):
    VERSION='0.2.0'
    firings=mlpr.Input('Firings file (sorting)')
    firings_true=mlpr.Input('True firings file')
    units_true=mlpr.IntegerListParameter('List of true units to consider')
    json_out=mlpr.Output('Table as .json file produced from pandas dataframe')
    html_out=mlpr.Output('Table as .html file produced from pandas dataframe')
    
    def run(self):
        sorting=SFMdaSortingExtractor(firings_file=self.firings)
        sorting_true=SFMdaSortingExtractor(firings_file=self.firings_true)
        if (self.units_true is not None) and (len(self.units_true)>0):
            sorting_true=si.SubSortingExtractor(parent_sorting=sorting_true,unit_ids=self.units_true)
        SC=SortingComparison(sorting_true,sorting)
        df=get_comparison_data_frame(comparison=SC)
        #sw.SortingComparisonTable(comparison=SC).getDataframe()
        json=df.transpose().to_dict()
        html=df.to_html(index=False)
        _write_json_file(json,self.json_out)
        _write_json_file(html,self.html_out)

def get_comparison_data_frame(*,comparison):
    import pandas as pd
    SC=comparison

    unit_properties=[] #snr, etc? these would need to be properties in the sortings of the comparison

    # Compute events counts
    sorting1=SC.getSorting1()
    sorting2=SC.getSorting2()
    unit1_ids = sorting1.getUnitIds()
    unit2_ids = sorting2.getUnitIds()
    N1 = len(unit1_ids)
    N2 = len(unit2_ids)
    event_counts1 = dict()
    for i1, u1 in enumerate(unit1_ids):
        times1 = sorting1.getUnitSpikeTrain(u1)
        event_counts1[u1] = len(times1)
    event_counts2 = dict()
    for i2, u2 in enumerate(unit2_ids):
        times2 = sorting2.getUnitSpikeTrain(u2)
        event_counts2[u2] = len(times2)

    rows = []
    for u_1, unit1 in enumerate(unit1_ids):
        unit2 = SC.getBestUnitMatch1(unit1)
        if unit2>=0:
            num_matches=SC.getMatchingEventCount(unit1, unit2)
            num_false_negatives=event_counts1[unit1]-num_matches
            num_false_positives=event_counts2[unit2]-num_matches
        else:
            num_matches=0
            num_false_negatives=event_counts1[unit1]
            num_false_positives=0
        row0 = {
            'unit_id': unit1,
            'accuracy': _safe_frac(num_matches,num_false_positives+num_false_negatives+num_matches),
            'best_unit': unit2,
            'matched_unit': SC.getMappedSorting1().getMappedUnitIds(unit1),
            'num_matches': num_matches,
            'num_false_negatives': num_false_negatives,
            'num_false_positives': num_false_positives,
            'f_n': _safe_frac(num_false_negatives,num_false_negatives+num_matches),
            'f_p': _safe_frac(num_false_positives,num_false_positives+num_matches)
        }
        for prop in unit_properties:
            pname = prop['name']
            row0[pname] = SC.getSorting1().getUnitProperty(unit_id=int(unit1), property_name=pname)
        rows.append(row0)

    df = pd.DataFrame(rows)
    fields = ['unit_id']
    fields = fields + ['accuracy', 'best_unit', 'matched_unit', 'num_matches', 'num_false_negatives', 'num_false_positives', 'f_n', 'f_p']
    for prop in unit_properties:
        pname = prop['name']
        fields.append(pname)
    df = df[fields]
    df['accuracy'] = df['accuracy'].map('{:,.4f}'.format)
    # df['Best match'] = df['Accuracy'].map('{:,.2f}'.format)
    df['f_n'] = df['f_n'].map('{:,.4f}'.format)
    df['f_p'] = df['f_p'].map('{:,.4f}'.format)
    return df

def _safe_frac(numer, denom):
    if denom == 0:
        return 0
    return float(numer) / denom

def _write_json_file(obj,path):
  with open(path,'w') as f:
    return json.dump(obj,f)


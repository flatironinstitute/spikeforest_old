import spikeextractors as si
#import spikewidgets as sw
import spiketoolkit as st
import mlprocessors as mlpr
import json
from kbucket import client as kb
import numpy as np

def compare_with_truth(result):
    ret={}
    units_true=result.get('units_true',[])
    out=GenSortingComparisonTable.execute(firings=result['firings'],firings_true=result['firings_true'],units_true=units_true,json_out={'ext':'.json'},html_out={'ext':'.html'}).outputs
    ret['json']=kb.saveFile(out['json_out'],basename='table.json')
    ret['html']=kb.saveFile(out['html_out'],basename='table.html')
    return ret

class GenSortingComparisonTable(mlpr.Processor):
    VERSION='0.2.0'
    firings=mlpr.Input('Firings file (sorting)')
    firings_true=mlpr.Input('True firings file')
    units_true=mlpr.IntegerListParameter('List of true units to consider')
    json_out=mlpr.Output('Table as .json file produced from pandas dataframe')
    html_out=mlpr.Output('Table as .html file produced from pandas dataframe')
    
    def run(self):
        sorting=si.MdaSortingExtractor(firings_file=self.firings)
        sorting_true=si.MdaSortingExtractor(firings_file=self.firings_true)
        if len(self.units_true)>0:
            sorting_true=si.SubSortingExtractor(parent_sorting=sorting_true,unit_ids=self.units_true)
        SC=st.comparison.SortingComparison(sorting_true,sorting)
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
        num_matches=SC.getMatchingEventCount(unit1, unit2)
        num_false_negatives=event_counts1[unit1]-num_matches
        num_false_positives=event_counts2[unit2]-num_matches
        row0 = {
            'unit_id': unit1,
            'accuracy': SC.getAgreementFraction(unit1, unit2),
            'best_unit': unit2,
            'matched_unit': SC.getMappedSorting1().getMappedUnitIds(unit1),
            'num_matches': num_matches,
            'num_false_negatives': num_false_negatives,
            'num_false_positives': num_false_positives,
            'f_n': _safe_frac(num_false_negatives,event_counts1[unit1]),
            'f_p': _safe_frac(num_false_positives,event_counts2[unit2])
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


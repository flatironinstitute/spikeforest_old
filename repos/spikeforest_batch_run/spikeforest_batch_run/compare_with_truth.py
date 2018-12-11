import spikeextractors as si
import spikewidgets as sw
import spiketoolkit as st
import mlprocessors as mlpr
import json
from kbucket import client as kb

def compare_with_truth(result):
    ret={}
    units_true=result.get('units_true',[])
    out=GenSortingComparisonTable.execute(firings=result['firings'],firings_true=result['firings_true'],units_true=units_true,json_out={'ext':'.json'},html_out={'ext':'.html'}).outputs
    ret['json']=kb.saveFile(out['json_out'],basename='table.json')
    ret['html']=kb.saveFile(out['html_out'],basename='table.html')
    return ret

class GenSortingComparisonTable(mlpr.Processor):
    VERSION='0.1.1'
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
        df=sw.SortingComparisonTable(comparison=SC).getDataframe()
        json=df.transpose().to_dict()
        html=df.to_html(index=False)
        _write_json_file(json,self.json_out)
        _write_json_file(html,self.html_out)

def _write_json_file(obj,path):
  with open(path,'w') as f:
    return json.dump(obj,f)

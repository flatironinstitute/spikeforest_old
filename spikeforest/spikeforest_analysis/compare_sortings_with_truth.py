# from spikeforest import spikewidgets as sw
import mlprocessors as mlpr
import json

import spikeextractors as si
import spiketoolkit as st
import pandas as pd
from .sfmdaextractors import SFMdaSortingExtractor
from .sortingcomparison import SortingComparison


# new method (in progress) that uses spiketoolkit
class GenSortingComparisonTableNew(mlpr.Processor):
    VERSION = '0.3.1'
    firings = mlpr.Input('Firings file (sorting)')
    firings_true = mlpr.Input('True firings file')
    units_true = mlpr.IntegerListParameter('List of true units to consider')
    json_out = mlpr.Output('Table as .json file produced from pandas dataframe')
    html_out = mlpr.Output('Table as .html file produced from pandas dataframe')
    # CONTAINER = 'sha1://5627c39b9bd729fc011cbfce6e8a7c37f8bcbc6b/spikeforest_basic.simg'
    # CONTAINER = 'sha1://0944f052e22de0f186bb6c5cb2814a71f118f2d1/spikeforest_basic.simg'  # MAY26JJJ
    CONTAINER = 'sha1://4904b8f914eb159618b6579fb9ba07b269bb2c61/06-26-2019/spikeforest_basic.simg'

    def run(self):
        print('GenSortingComparisonTable: firings={}, firings_true={}, units_true={}'.format(self.firings, self.firings_true, self.units_true))
        sorting = SFMdaSortingExtractor(firings_file=self.firings)
        sorting_true = SFMdaSortingExtractor(firings_file=self.firings_true)
        if (self.units_true is not None) and (len(self.units_true) > 0):
            sorting_true = si.SubSortingExtractor(parent_sorting=sorting_true, unit_ids=self.units_true)

        SC = st.comparison.compare_sorter_to_ground_truth(
            gt_sorting=sorting_true,
            tested_sorting=sorting,
            delta_time=0.3,
            min_accuracy=0,
            compute_misclassification=False,
            exhaustive_gt=False  # Fix this in future
        )
        df = pd.concat([SC.count, SC.get_performance()], axis=1).reset_index()

        df = df.rename(columns=dict(
            gt_unit_id='unit_id',
            fp='num_false_positives',
            fn='num_false_negatives',
            tested_id='best_unit',
            tp='num_matches'
        ))
        df['matched_unit'] = df['best_unit']
        df['f_p'] = 1 - df['precision']
        df['f_n'] = 1 - df['recall']

        # sw.SortingComparisonTable(comparison=SC).getDataframe()
        json = df.transpose().to_dict()
        html = df.to_html(index=False)
        _write_json_file(json, self.json_out)
        _write_json_file(html, self.html_out)


# old method that uses spikeforest
class GenSortingComparisonTable(mlpr.Processor):
    VERSION = '0.2.6'
    firings = mlpr.Input('Firings file (sorting)')
    firings_true = mlpr.Input('True firings file')
    units_true = mlpr.IntegerListParameter('List of true units to consider')
    json_out = mlpr.Output('Table as .json file produced from pandas dataframe')
    html_out = mlpr.Output('Table as .html file produced from pandas dataframe')
    # CONTAINER = 'sha1://5627c39b9bd729fc011cbfce6e8a7c37f8bcbc6b/spikeforest_basic.simg'
    # CONTAINER = 'sha1://0944f052e22de0f186bb6c5cb2814a71f118f2d1/spikeforest_basic.simg'  # MAY26JJJ
    CONTAINER = 'sha1://4904b8f914eb159618b6579fb9ba07b269bb2c61/06-26-2019/spikeforest_basic.simg'

    def run(self):
        print('GenSortingComparisonTable: firings={}, firings_true={}, units_true={}'.format(self.firings, self.firings_true, self.units_true))
        sorting = SFMdaSortingExtractor(firings_file=self.firings)
        sorting_true = SFMdaSortingExtractor(firings_file=self.firings_true)
        if (self.units_true is not None) and (len(self.units_true) > 0):
            sorting_true = si.SubSortingExtractor(parent_sorting=sorting_true, unit_ids=self.units_true)

        SC = SortingComparison(sorting_true, sorting, delta_tp=30)
        df = get_comparison_data_frame(comparison=SC)
        # sw.SortingComparisonTable(comparison=SC).getDataframe()
        json = df.transpose().to_dict()
        html = df.to_html(index=False)
        _write_json_file(json, self.json_out)
        _write_json_file(html, self.html_out)


def get_comparison_data_frame(*, comparison):
    import pandas as pd
    SC = comparison

    unit_properties = []  # snr, etc? these would need to be properties in the sortings of the comparison

    # Compute events counts
    sorting1 = SC.getSorting1()
    sorting2 = SC.getSorting2()
    unit1_ids = sorting1.get_unit_ids()
    unit2_ids = sorting2.get_unit_ids()
    # N1 = len(unit1_ids)
    # N2 = len(unit2_ids)
    event_counts1 = dict()
    for _, u1 in enumerate(unit1_ids):
        times1 = sorting1.get_unit_spike_train(u1)
        event_counts1[u1] = len(times1)
    event_counts2 = dict()
    for _, u2 in enumerate(unit2_ids):
        times2 = sorting2.get_unit_spike_train(u2)
        event_counts2[u2] = len(times2)

    rows = []
    for _, unit1 in enumerate(unit1_ids):
        unit2 = SC.getBestUnitMatch1(unit1)
        if unit2 >= 0:
            num_matches = SC.getMatchingEventCount(unit1, unit2)
            num_false_negatives = event_counts1[unit1] - num_matches
            num_false_positives = event_counts2[unit2] - num_matches
        else:
            num_matches = 0
            num_false_negatives = event_counts1[unit1]
            num_false_positives = 0
        row0 = {
            'unit_id': unit1,
            'accuracy': _safe_frac(num_matches, num_false_positives + num_false_negatives + num_matches),
            'best_unit': unit2,
            'matched_unit': SC.getMappedSorting1().getMappedUnitIds(unit1),
            'num_matches': num_matches,
            'num_false_negatives': num_false_negatives,
            'num_false_positives': num_false_positives,
            'f_n': _safe_frac(num_false_negatives, num_false_negatives + num_matches),
            'f_p': _safe_frac(num_false_positives, num_false_positives + num_matches)
        }
        for prop in unit_properties:
            pname = prop['name']
            row0[pname] = SC.getSorting1().get_unit_property(unit_id=int(unit1), property_name=pname)
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


def _write_json_file(obj, path):
    with open(path, 'w') as f:
        return json.dump(obj, f)

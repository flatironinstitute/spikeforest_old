import vdomr as vd
import spikeforest as sf
from kbucket import client as kb
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt


class AccuracyPlot(vd.components.Pyplot):
    def __init__(self, snrs, accuracies):
        vd.components.Pyplot.__init__(self)
        self._snrs = snrs
        self._accuracies = accuracies

    def plot(self):
        plt.scatter(self._snrs, self._accuracies)


class StudySorterFigure(vd.Component):
    def __init__(self, sfdata):
        vd.Component.__init__(self)
        self._plot = None
        self._SF_data = sfdata
        self._study = None
        self._sorter = None

    def setStudySorter(self, *, study, sorter):
        self._study = study
        self._sorter = sorter
        self._update_plot()

    def _update_plot(self):
        SF = self._SF_data
        study = SF.study(self._study)
        b = _get_study_sorting_results(study)
        a = b[self._sorter]
        snrs = a['true_unit_snrs']
        accuracies = a['num_matches'] / \
            (a['num_matches']+a['num_false_positives']+a['num_false_negatives'])

        self._plot = AccuracyPlot(snrs, accuracies)
        self.refresh()

    def render(self):
        if self._plot is None:
            return vd.div('Nothing')
        return vd.div(
            vd.div('test '+self._study+' '+self._sorter),
            self._plot
        )


class SFBrowser(vd.Component):
    def __init__(self, group):
        vd.Component.__init__(self)

        self._sorter_names = kb.loadObject(
            key=dict(name='spikeforest_sorter_names')
        )

        group_name = group
        self._group = group_name

        a = kb.loadObject(
            key=dict(name='summarized_recordings', group_name=group_name)
        )
        if not a:
            print('ERROR: unable to open recording group: '+group_name)
            return

        if ('recordings' not in a) or ('studies' not in a):
            print('ERROR: problem with recording group: '+group_name)
            return

        studies = a['studies']
        recordings = a['recordings']

        SF = sf.SFData()
        SF.loadStudies(studies)
        SF.loadRecordings2(recordings)

        sorter_names = self._sorter_names[group_name]
        for sorter_name in sorter_names:
            print('Loading sorting results for sorter: '+sorter_name)
            b = kb.loadObject(
                key=dict(name='sorting_results',
                         group_name=group_name, sorter_name=sorter_name)
            )
            if not b:
                print('WARNING: unable to open sorting results for sorter: '+sorter_name)
                break
            SF.loadSortingResults(b['sorting_results'])

        self._SF_data = SF

        self._accuracy_threshold_input = vd.components.LineEdit(
            value=0.8, dtype=float, style=dict(width='70px'))
        self._update_button = vd.components.Button(
            onclick=self._on_update, class_='button', label='Update')
        self._study_sorter_fig = StudySorterFigure(SF)
        self._study_sorter_table = vd.div()  # dummy

        vd.devel.loadBootstrap()

        self._update_accuracy_table()

    def _on_update(self):
        self._update_accuracy_table()

    def _update_accuracy_table(self):
        accuracy_threshold = self._accuracy_threshold_input.value()
        self._accuracy_table_data, self._sorters = self._get_accuracy_table_data(
            accuracy_threshold=accuracy_threshold)
        self._accuracy_table = self._to_table(
            self._accuracy_table_data, ['study']+self._sorters)
        self.refresh()

    def _open_study_sorter_fig(self, *, sorter, study):
        self._study_sorter_fig.setStudySorter(study=study, sorter=sorter)

    def _get_accuracy_table_data(self, *, accuracy_threshold):
        SF = self._SF_data
        accuracy_table = []
        sorters = set()
        for sname in SF.studyNames():
            print('STUDY: '+sname)
            study = SF.study(sname)
            b = _get_study_sorting_results(study)
            tmp = dict(
                study=dict(  # first column
                    text=sname
                )
            )
            for sorter in b:
                sorters.add(sorter)
                a = b[sorter]
                accuracies = a['num_matches'] / \
                    (a['num_matches']+a['num_false_positives'] +
                     a['num_false_negatives'])
                tmp[sorter] = dict(
                    text=str(np.count_nonzero(
                        accuracies >= accuracy_threshold)),
                    callback=lambda sorter=sorter, study=sname: self._open_study_sorter_fig(
                        sorter=sorter, study=study)
                )
            accuracy_table.append(tmp)

        sorters = list(sorters)
        sorters.sort()
        return accuracy_table, sorters

    def _to_table(self, X, column_names):
        rows = []
        rows.append(vd.tr([vd.th(cname) for cname in column_names]))
        for x in X:
            elmts = []
            for cname in column_names:
                tmp = x.get(cname)
                if tmp:
                    if 'callback' in tmp:
                        elmt = vd.a(tmp['text'], onclick=tmp['callback'])
                    else:
                        elmt = vd.span(tmp['text'])
                else:
                    elmt = vd.span('N/A')
                elmts.append(elmt)
            rows.append(vd.tr([vd.td(elmt) for elmt in elmts]))
        return vd.table(rows, class_='table')

    def render(self):
        SF = self._SF_data

        return vd.div(
            vd.table(
                vd.tr(
                    vd.td('Accuracy threshold:'),
                    vd.td(self._accuracy_threshold_input),
                    vd.td(self._update_button)
                ),
                class_='table',
                style={'max-width': '200px'}
            ),
            vd.components.ScrollArea(
                self._accuracy_table,
                height=500
            ),
            self._study_sorter_fig,
            style=dict(padding='15px')
        )


def _get_study_sorting_results(study):
    results = []
    for rname in study.recordingNames():
        rec = study.recording(rname)
        true_units_info = rec.trueUnitsInfo(format='json')
        true_units_info_by_id = dict()
        for true_unit in true_units_info:
            true_units_info_by_id[true_unit['unit_id']] = true_unit
        for srname in rec.sortingResultNames():
            a = rec.sortingResult(srname)
            res0 = dict(sorter=srname, recording=rname, study=study.name())
            tmp = a.comparisonWithTruth(format='json')
            for i in tmp:
                tmp[i]['true_unit_info'] = true_units_info_by_id[tmp[i]['unit_id']]
            res0['comparison_with_truth'] = tmp
            results.append(res0)

    sorters = list(set([a['sorter'] for a in results]))
    sorters.sort()

    units_by_sorter = dict()
    for sorter in sorters:
        units_by_sorter[sorter] = []

    for obj in results:
        sorter0 = obj['sorter']
        units = [obj['comparison_with_truth'][i]
                 for i in obj['comparison_with_truth']]
        units_by_sorter[sorter0] = units_by_sorter[sorter0]+units

    ret = dict()
    for sorter in sorters:
        units = units_by_sorter[sorter]
        try:
            ret[sorter] = dict(
                true_unit_ids=[unit['unit_id'] for unit in units],
                true_unit_snrs=np.array(
                    [unit['true_unit_info']['snr'] for unit in units]),
                true_unit_firing_rates=np.array(
                    [unit['true_unit_info']['firing_rate'] for unit in units]),
                num_matches=np.array([unit['num_matches'] for unit in units]),
                num_false_positives=np.array(
                    [unit['num_false_positives'] for unit in units]),
                num_false_negatives=np.array(
                    [unit['num_false_negatives'] for unit in units])
            )
        except:
            print('WARNING: Problem loading results for sorter: '+sorter)
            ret[sorter] = dict(
                true_unit_ids=[],
                true_unit_snrs=np.array([]),
                true_unit_firing_rates=np.array([]),
                num_matches=np.array([]),
                num_false_positives=np.array([]),
                num_false_negatives=np.array([])
            )

    return ret

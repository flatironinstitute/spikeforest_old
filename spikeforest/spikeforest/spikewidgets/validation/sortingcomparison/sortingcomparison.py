import numpy as np
import spikeextractors as se
from scipy.optimize import linear_sum_assignment


class SortingComparison():
    def __init__(self, sorting1, sorting2, delta_tp=20):
        self._sorting1 = sorting1
        self._sorting2 = sorting2
        self._delta_tp = delta_tp
        self._do_comparison()

    def getSorting1(self):
        return self._sorting1

    def getSorting2(self):
        return self._sorting2

    def getMappedSorting1(self):
        return MappedSortingExtractor(self._sorting1, self._unit_map12)

    def getMappedSorting2(self):
        return MappedSortingExtractor(self._sorting2, self._unit_map21)

    def getMatchingEventCount(self, unit1, unit2):
        if (unit1 is not None) and (unit2 is not None):
            a = self._matching_event_counts_12[unit1]
            if unit2 in a:
                return a[unit2]
            else:
                return 0
        # else if unit1 is not None:
        #    return self._missed_event_counts_1[unit1]
        # else if unit2 is not None:
        #    return self._missed_event_counts_2[unit2]
        else:
            raise Exception('getMatchingEventCount: unit1 and unit2 must not be None.')

    def _compute_agreement_score(self, num_matches, num1, num2):
        denom = num1 + num2 - num_matches
        if denom == 0:
            return 0
        return num_matches / denom

    def _compute_safe_frac(self, numer, denom):
        if denom == 0:
            return 0
        return numer / denom

    def getBestUnitMatch1(self, unit1):
        if unit1 in self._best_match_units_12:
            return self._best_match_units_12[unit1]
        else:
            return None

    def getBestUnitMatch2(self, unit2):
        if unit2 in self._best_match_units_21:
            return self._best_match_units_21[unit2]
        else:
            return None

    def getMatchingUnitList1(self, unit1):
        a = self._matching_event_counts_12[unit1]
        return list(a.keys())

    def getMatchingUnitList2(self, unit2):
        a = self._matching_event_counts_21[unit2]
        return list(a.keys())

    def getAgreementFraction(self, unit1=None, unit2=None):
        if (unit1 is not None) and (unit2 is None):
            unit2 = self.getBestUnitMatch1(unit1)
            if unit2 is None:
                return 0
        if (unit1 is None) and (unit2 is not None):
            unit1 = self.getBestUnitMatch2(unit2)
            if unit1 is None:
                return 0
        if (unit1 is None) and (unit2 is None):
            raise Exception('getAgreementFraction: at least one of unit1 and unit2 must not be None.')

        a = self._matching_event_counts_12[unit1]
        if unit2 not in a:
            return 0
        return self._compute_agreement_score(a[unit2], self._event_counts_1[unit1], self._event_counts_2[unit2])

    def getFalsePositiveFraction(self, unit1, unit2=None):
        if unit1 is None:
            raise Exception('getFalsePositiveFraction: unit1 must not be None')
        if unit2 is None:
            unit2 = self.getBestUnitMatch1(unit1)
            if unit2 is None:
                return 0

        a = self._matching_event_counts_12[unit1]
        if unit2 not in a:
            return 0
        return 1 - self._compute_safe_frac(a[unit2], self._event_counts_1[unit1])

    def getFalseNegativeFraction(self, unit1, unit2=None):
        if unit1 is None:
            raise Exception('getFalsePositiveFraction: unit1 must not be None')
        if unit2 is None:
            unit2 = self.getBestUnitMatch1(unit1)
            if unit2 is None:
                return 0

        a = self._matching_event_counts_12[unit1]
        if unit2 not in a:
            return 0
        return 1 - self._compute_safe_frac(a[unit2], self._event_counts_2[unit2])

    def _do_comparison(self):
        self._event_counts_1 = dict()
        self._event_counts_2 = dict()
        self._matching_event_counts_12 = dict()
        self._best_match_units_12 = dict()
        self._matching_event_counts_21 = dict()
        self._best_match_units_21 = dict()
        self._unit_map12 = dict()
        self._unit_map21 = dict()

        sorting1 = self._sorting1
        sorting2 = self._sorting2
        unit1_ids = sorting1.getUnitIds()
        unit2_ids = sorting2.getUnitIds()
        N1 = len(unit1_ids)
        N2 = len(unit2_ids)
        event_counts1 = np.zeros((N1)).astype(np.int64)
        for i1, u1 in enumerate(unit1_ids):
            times1 = sorting1.getUnitSpikeTrain(u1)
            event_counts1[i1] = len(times1)
            self._event_counts_1[u1] = len(times1)
        event_counts2 = np.zeros((N2)).astype(np.int64)
        for i2, u2 in enumerate(unit2_ids):
            times2 = sorting2.getUnitSpikeTrain(u2)
            event_counts2[i2] = len(times2)
            self._event_counts_2[u2] = len(times2)
        matching_event_counts = np.zeros((N1, N2)).astype(np.int64)
        scores = np.zeros((N1, N2))
        for i1, u1 in enumerate(unit1_ids):
            times1 = sorting1.getUnitSpikeTrain(u1)
            for i2, u2 in enumerate(unit2_ids):
                times2 = sorting2.getUnitSpikeTrain(u2)
                num_matches = count_matching_events(times1, times2, delta=self._delta_tp)
                matching_event_counts[i1, i2] = num_matches
                scores[i1, i2] = self._compute_agreement_score(num_matches, event_counts1[i1], event_counts2[i2])

        for i1, u1 in enumerate(unit1_ids):
            scores0 = scores[i1, :]
            self._matching_event_counts_12[u1] = dict()
            if np.max(scores0) > 0:
                inds0 = np.where(scores0 > 0)[0]
                for i2 in inds0:
                    self._matching_event_counts_12[u1][unit2_ids[i2]] = matching_event_counts[i1, i2]
                i2_best = np.argmax(scores0)
                self._best_match_units_12[u1] = unit2_ids[i2_best]
            else:
                self._best_match_units_12[u1] = None

        for i2, u2 in enumerate(unit2_ids):
            scores0 = scores[:, i2]
            self._matching_event_counts_21[u2] = dict()
            if np.max(scores0) > 0:
                inds0 = np.where(scores0 > 0)[0]
                for i1 in inds0:
                    self._matching_event_counts_21[u2][unit1_ids[i1]] = matching_event_counts[i1, i2]
                i1_best = np.argmax(scores0)
                self._best_match_units_21[u1] = unit1_ids[i1_best]
            else:
                self._best_match_units_21[u1] = None

        [inds1, inds2] = linear_sum_assignment(-scores)
        inds1 = list(inds1)
        inds2 = list(inds2)
        k2 = np.max(unit2_ids) + 1
        for i1, u1 in enumerate(unit1_ids):
            if i1 in inds1:
                aa = inds1.index(i1)
                i2 = inds2[aa]
                u2 = unit2_ids[i2]
                self._unit_map12[u1] = u2
            else:
                self._unit_map12[u1] = k2
                k2 = k2 + 1
        k1 = np.max(unit1_ids) + 1
        for i2, u2 in enumerate(unit2_ids):
            if i2 in inds2:
                aa = inds2.index(i2)
                i1 = inds1[aa]
                u1 = unit1_ids[i1]
                self._unit_map21[u2] = u1
            else:
                self._unit_map21[u2] = k1
                k1 = k1 + 1


class MappedSortingExtractor(se.SortingExtractor):
    def __init__(self, sorting, unit_map):
        se.SortingExtractor.__init__(self)
        self._sorting = sorting
        self._unit_map = unit_map
        self._reverse_map = dict()
        for key in unit_map:
            self._reverse_map[unit_map[key]] = key
        units = sorting.getUnitIds()
        self._unit_ids = list(np.sort([self._unit_map[unit] for unit in units]))

    def getUnitIds(self):
        return self._unit_ids

    def getUnitSpikeTrain(self, unit_id, start_frame=None, end_frame=None):
        unit2 = self._reverse_map[unit_id]
        return self._sorting.getUnitSpikeTrain(unit2, start_frame=start_frame, end_frame=end_frame)


def count_matching_events(times1, times2, delta=20):
    times_concat = np.concatenate((times1, times2))
    membership = np.concatenate((np.ones(times1.shape) * 1, np.ones(times2.shape) * 2))
    indices = times_concat.argsort()
    times_concat_sorted = times_concat[indices]
    membership_sorted = membership[indices]
    diffs = times_concat_sorted[1:] - times_concat_sorted[:-1]
    inds = np.where((diffs <= delta) & (membership_sorted[0:-1] != membership_sorted[1:]))[0]
    if (len(inds) == 0):
        return 0
    inds2 = np.where(inds[:-1] + 1 != inds[1:])[0]
    return len(inds2) + 1

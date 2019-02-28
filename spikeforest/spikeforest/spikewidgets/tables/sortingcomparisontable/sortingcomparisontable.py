import pandas as pd
from IPython.display import HTML


class SortingComparisonTable():
    def __init__(self, comparison, reference=1, unit_properties=[]):
        self._comparison = comparison
        self._unit_properties = unit_properties
        self._reference = reference
        for i in range(len(self._unit_properties)):
            prop = self._unit_properties[i]
            if type(prop) != dict:
                self._unit_properties[i] = {'name': prop}

    def getDataframe(self):
        SC = self._comparison
        rows = []
        if self._reference == 1:
            for u_1, unit1 in enumerate(SC.getSorting1().getUnitIds()):
                unit2 = SC.getBestUnitMatch1(unit1)
                row0 = {
                    'unit_id': unit1,
                    'accuracy': SC.getAgreementFraction(unit1, unit2),
                    'best_unit': unit2,
                    'matched_unit': SC.getMappedSorting1().getMappedUnitIds(unit1),
                    'num_matches': SC.getMatchingEventCount(unit1, unit2),
                    'f_n': SC.getFalseNegativeFraction(unit1),
                    'f_p': SC.getFalsePositiveFraction(unit1),
                }
                for prop in self._unit_properties:
                    pname = prop['name']
                    row0[pname] = SC.getSorting1().getUnitProperty(unit_id=int(unit1), property_name=pname)
                rows.append(row0)
        elif self._reference == 2:
            for u_1, unit1 in enumerate(SC.getSorting2().getUnitIds()):
                unit2 = SC.getBestUnitMatch2(unit1)
                row0 = {
                    'unit_id': unit1,
                    'accuracy': SC.getAgreementFraction(unit2, unit1),
                    'best_unit': unit2,
                    'matched_unit': SC.getMappedSorting2().getMappedUnitIds(unit1),
                    'num_matches': SC.getMatchingEventCount(unit2, unit1),
                    'f_n': SC.getFalseNegativeFraction(unit1),
                    'f_p': SC.getFalsePositiveFraction(unit1),
                }
                for prop in self._unit_properties:
                    pname = prop['name']
                    row0[pname] = SC.getSorting2().getUnitProperty(unit_id=int(unit1), property_name=pname)
                rows.append(row0)

        df = pd.DataFrame(rows)
        fields = ['unit_id']
        fields = fields + ['accuracy', 'best_unit', 'matched_unit', 'f_n', 'f_p', 'num_matches']
        for prop in self._unit_properties:
            pname = prop['name']
            fields.append(pname)
        df = df[fields]
        df['accuracy'] = df['accuracy'].map('{:,.2f}'.format)
        # df['Best match'] = df['Accuracy'].map('{:,.2f}'.format)
        df['f_n'] = df['f_n'].map('{:,.2f}'.format)
        df['f_p'] = df['f_p'].map('{:,.2f}'.format)
        return df

    def display(self):
        df = self.getDataframe()
        display(HTML(df.to_html(index=False)))

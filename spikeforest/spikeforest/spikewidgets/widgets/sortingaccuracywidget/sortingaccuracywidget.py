from matplotlib import pyplot as plt
import numpy as np


class SortingAccuracyWidget:
    def __init__(self, *, sorting_comparison, property_name=None):
        self._SC = sorting_comparison
        self._property_name = property_name

    def plot(self, mode='accuracy'):
        if mode == 'all':
            fig=plt.figure(figsize=(12,3))
            self._do_plot(ax=fig.add_subplot(1,3,1), show=False)
            self._do_plot_recall(ax=fig.add_subplot(1,3,2), show=False)
            self._do_plot_precision(ax=fig.add_subplot(1,3,3), show=False)
            plt.show()
        else:
            fig=plt.figure(figsize=(4,3))
            ax = fig.add_subplot(1,1,1)
            if mode == 'accuracy':
                self._do_plot(ax=ax)
            elif mode == 'recall' or mode == 'sensitivity':
                self._do_plot_recall(ax=ax)
            elif mode == 'precision':
                self._do_plot_precision(ax=ax)


    def _do_plot(self, ax=None, accuracy_thresh=.8, show=True):
        SC = self._SC
        units = SC.getSorting1().getUnitIds()
        agreements = [SC.getAgreementFraction(unit) for unit in units]
        if self._property_name:
            xvals = SC.getSorting1().getUnitsProperty(unit_ids=units, property_name=self._property_name)
            ax.plot(xvals, agreements, '.')
            plt.xlabel(self._property_name)
        else:
            ax.plot(agreements, '.')
            plt.xticks([])

        plt.ylabel('Accuracy')
        plt.ylim(0,1)
        nUnits_above = np.sum(np.array(agreements) >= accuracy_thresh)
        plt.title('{} units > {} accuracy'.format(nUnits_above, accuracy_thresh))
        if show: plt.show()


    def _do_plot_recall(self, ax=None, recall_thresh=.8, show=True):
        SC = self._SC

        units = SC.getSorting1().getUnitIds()
        recall = [1-SC.getFalsePositiveFraction(unit) for unit in units]
        if self._property_name:
            xvals = SC.getSorting1().getUnitsProperty(unit_ids=units, property_name=self._property_name)
            ax.plot(xvals, recall, '.')
            plt.xlabel(self._property_name)
        else:
            ax.plot(recall, '.')
            plt.xticks([])

        plt.ylabel('Recall')
        plt.ylim(0,1)
        nUnits_above = np.sum(np.array(recall) >= recall_thresh)
        plt.title('{} units > {} Recall'.format(nUnits_above, recall_thresh))
        if show: plt.show()


    def _do_plot_precision(self, ax=None, precision_thresh=.8, show=True):
        SC = self._SC

        units = SC.getSorting1().getUnitIds()
        precision = [1-SC.getFalseNegativeFraction(unit) for unit in units]
        if self._property_name:
            xvals = SC.getSorting1().getUnitsProperty(unit_ids=units, property_name=self._property_name)
            ax.plot(xvals, precision, '.')
            plt.xlabel(self._property_name)
        else:
            ax.plot(precision, '.')
            plt.xticks([])

        plt.ylabel('Precision')
        plt.ylim(0,1)
        nUnits_above = np.sum(np.array(precision) >= precision_thresh)
        plt.title('{} units > {} precision'.format(nUnits_above, precision_thresh))
        if show: plt.show()

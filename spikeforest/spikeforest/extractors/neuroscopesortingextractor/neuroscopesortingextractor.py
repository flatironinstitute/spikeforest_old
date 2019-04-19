from spikeextractors import SortingExtractor
import numpy as np

class NeuroscopeSortingExtractor(SortingExtractor):
    """
    Extracts sorting information from pair of .res and .clu files . The .res is a text file with
    a sorted list of all spiketimes from all units displayed in sample (integer '%i') units. 
    The .clu file is a file with one more row than the .res with the first row corresponding to
    the total number of unit ids and the rest of the rows indicating which unit id the corresponding
    entry in the .res file refers to.

    Parameters
    ----------
    resfile : str
	Path to the .res text file.
    clufile : str
	Path to the .clu text file.
    """
    def __init__(self, resfile, clufile):
        SortingExtractor.__init__(self)
        res = np.loadtxt(resfile, dtype=np.int64, usecols=0, ndmin=1)
        clu = np.loadtxt(clufile, dtype=np.int64, usecols=0, ndmin=1)
        if len(res) > 0:
            n_clu = clu[0]
            clu = np.delete(clu,0)
            self._spiketrains = []
            self._unit_ids = list(x+1 for x in range(n_clu))
            for s_id in self._unit_ids:
                self._spiketrains.append(res[(clu == s_id).nonzero()])
        else:
            self._spiketrains = []
            self._unit_ids = []
        
    def getUnitIds(self):
        return list(self._unit_ids)

    def getUnitSpikeTrain(self, unit_id, start_frame=None, end_frame=None):
        if start_frame is None:
            start_frame = 0
        if end_frame is None:
            end_frame = np.Inf
        times = self._spiketrains[self.getUnitIds().index(unit_id)]
        inds = np.where((start_frame <= times) & (times < end_frame))
        return times[inds]

    @staticmethod
    def writeSorting(sorting, save_path):
        save_res = "{}.res".format(save_path)
        save_clu = "{}.clu".format(save_path)
        
        unit_ids = sorting.getUnitIds()
        spiketrains = [sorting.getUnitSpikeTrain(u) for u in unit_ids]
        res = np.concatenate(spiketrains).ravel()
        clu = np.concatenate([np.repeat(i+1,len(st)) for i,st in enumerate(spiketrains)]).ravel()
        res_sort = np.argsort(res)
        res = res[res_sort]
        clu = clu[res_sort]
        clu = np.insert(clu, 0, len(unit_ids))

        np.savetxt(save_res, res, fmt='%i')
        np.savetxt(save_clu, clu, fmt='%i')
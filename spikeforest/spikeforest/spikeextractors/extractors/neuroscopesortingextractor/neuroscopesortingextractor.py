from ....spikeextractors import SortingExtractor
import numpy as np

class NeuroscopeSortingExtractor(SortingExtractor):
    def __init__(self, resfile, clufile):
        SortingExtractor.__init__(self)
        res = np.loadtxt(resfile, dtype=np.int64, usecols=0)
        clu = np.loadtxt(clufile, dtype=np.int64, usecols=0)
        n_clu = clu[0]
        clu = np.delete(clu,0)
        self._spiketrains = [np.zeros(0, dtype=np.int64) for range(n_clu)]
        self._unit_ids = list(range(n_clu))
        for (spike, s_id) in zip(res, clu):
            self._spiketrains[s_id-1].append(res)

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

        res = np.concatenate(self._spiketrains).ravel()
        clu = np.concatenate(np.repeat(i+1,len(st)) for i,st in enumerate(self._spiketrains)).ravel()
        clu = np.insert(clu, 0, len(self._unit_ids))

        np.savetxt(save_res, res)
        np.savetxt(save_clu, clu)

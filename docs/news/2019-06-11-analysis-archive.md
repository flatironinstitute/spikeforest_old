---
title: Analysis archive
date: 2019-06-11
author: Jeremy Magland
---

SpikeForest now has an analysis archive. You can click on the "Archive" link at
the top of the website and get a listing of the current analysis and all
previous analyses (as of a few days ago). Each entry is a snapshot of the entire
analysis, including the results of all sorters applied to all recordings, all
the input files, parameters, outputs, singularity containers, etc. Although it
seems like a lot of data, the actual snapshot is just a JSON file containing
`sha1://` and `sha1dir://` links to the larger files. It's sort of like an
index.

To download and explore the results of a particular analysis, first find the
desired file in the list and copy the `sha1://` path. Then load it into Python
(perhaps a notebook) as follows (substituting the path you copied of course):

```
from mountaintools import client as mt

mt.configDownloadFrom(['spikeforest.public'])
A = mt.loadObject(path='sha1://60d72c800e62b86afac17182fcd8c27f1d53d2fd/analysis.json')
```

We can begin exploring this object by printing some general information:

```
print(A['General'])

print('\nSorters used:')
print([sorter['name'] for sorter in A['Sorters']])

print('\nStudy sets:')
print([study_set['name'] for study_set in A['StudySets']])
```

This outputs:

```
[{'dateUpdated': '2019-06-10T12:57:51.276958', 'packageVersions': {'mountaintools': '0.4.1', 'spikeforest': '0.8.1'}}]

Sorters used:
['HerdingSpikes2', 'IronClust', 'JRClust', 'KiloSort', 'KiloSort2', 'Klusta', 'MountainSort4', 'SpykingCircus', 'Tridesclous', 'Waveclus']

Study sets:
['PAIRED_BOYDEN', 'PAIRED_CRCNS_HC1', 'PAIRED_MEA64C_YGER', 'PAIRED_KAMPFF', 'PAIRED_MONOTRODE', 'SYNTH_MONOTRODE', 'SYNTH_BIONET', 'SYNTH_MAGLAND', 'MANUAL_FRANKLAB', 'SYNTH_MEAREC_NEURONEXUS', 'SYNTH_MEAREC_TETRODE', 'SYNTH_VISAPY', 'HYBRID_JANELIA']
```
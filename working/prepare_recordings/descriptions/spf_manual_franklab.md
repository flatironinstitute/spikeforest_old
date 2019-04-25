---
# This is YAML front matter
label: SPF_MANUAL_FRANKLAB
electrode_type: needed
doi: needed
ground_truth: human
recording_type: in-vivo
organism: needed
---

# SPF_MANUAL_FRANKLAB

Tetrode manual sorting by three human sorters. Dataset prepared by Jason Chung from Loren Frank's lab.

## Recording format
- int16, 30000 samples/s, tetrode (four channels), negative going spikes
- Recording is divided to 600, 1200, and 2400s durations. 

Studyset is prepared by James Jun (2018 Dec 21)

## Naming convention
- tetrode_600s: each recording is 600s long. This folder contains four time segments
- tetrode_1200s: each recording is 1200s long. This folder contains two time segments
- tetrode_2400s: each recording is 2400s long. This folder contains one time segments
- sorter1_2: sorted by a human sorter #1 and 2nd time segment
- sorter2_3: sorted by a human sorter #2 and 3rd time segment

## Publication
- Chung JE, Magland JF, Barnett AH, Tolosa VM, Tooker AC, Lee KY, Shah KG, Felix SH, Frank LM, Greengard LF. A fully automated approach to spike sorting. Neuron. 2017 Sep 13;95(6):1381-94.
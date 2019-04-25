---
# This is YAML front matter
label: SPF_SYNTH_BIONET
electrode_type: silicon-probe
doi: TODO: cite bionet paper Allen institute
ground_truth: simulation
organism: rat neuron models from blue brain project
source: Catalin Mitelut, Allen Institute for Brain Science
labels:
  - in-silico
---

# SPF_SYNTH_BIONET

Original data (4 minutes) was generated using Bionet simulator. Data was concatenated 4-fold with random noise (10 microvolts RMS) to yield 16 minutes of data.

## Studies

* bionet_static
  - no drift added

* bionet_drift
  - uniform drift added, translating 20 micrometers over the duration of the recording

* bionet_shuffle
  - random shuffling was added to the drift data

More details can be found: TODO: link to some description or code.


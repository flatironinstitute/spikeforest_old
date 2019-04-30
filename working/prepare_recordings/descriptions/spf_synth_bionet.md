---
# This is YAML front matter
label: SPF_SYNTH_BIONET
electrode_type: silicon-probe
doi: 
  - 10.1371/journal.pone.0201630
  - 10.1101/101030
ground_truth: simulation
organism: rat neuron models from blue brain project
source: Catalin Mitelut, Allen Institute for Brain Science
labels:
  - in-silico
---

# SPF_SYNTH_BIONET

## Synthetic groundtruth generated using Bionet simulator
- Bionet is a neuron-based network simulator
- Original data (4 minutes) was generated using Bionet simulator (noiseless). 
- Data was concatenated 4-fold with random noise (10 microvolts RMS) to yield 16 minutes of data.

## Detailed simulation method (originally described in Jun et al, 2017, bioRxiv)
Our biophysical simulation randomly distributed ~710 neurons within a sensing volume of the probe (200×200×600 μm), and each neuron is constructed from real morphology of various cell types. Our simulation closely matches the real recordings in terms of the spatial spread of the spike waveforms, and the identity of all units and their spike timing information are precisely determined from their simulated intracellular voltage traces. Biophysically realistic network simulations were setup in order to generate simulated ground truth extracellular depth recordings datasets. The main engine used for these biophysical simulations was NEURON version 7.4 used with custom-written python (version 2.7) wrapper-algorithms that were used to define, setup and instantiate network models and simulations as well as save output.

The network model consists of two cell types, excitatory pyramidal neurons (2,560) and inhibitory basket cells (640). Pyramidal single-neuron models used in our network were published by Hay and co-workers as part of their study on models capturing a wide range of dendritic and perisomatic active properties. These single-neuron models were shown to capture a number of intracellular characteristics such as backpropagating action potentials, dendritic Calcium electrogenesis, etc. In addition, a later study showed that these computational models accurately capture the extracellular signature of neocortical pyramidal neurons. We adopted inhibitory basket cell models from Hu et al. (2010) who developed these models to capture a number of features such as backpropagation and dendritic Na/K ratio. Notably, pyramidal and basket cell models had active dendrites, a feature critical for capturing extracellular spiking activity. Each neuron received external excitatory synaptic input emulating AMPA synapses. The number and timing of these external synaptic inputs was set such as to reach specific spike frequency output.

With regards to calculating the simulated extracellular recordings, the so-called line source approximation was used to estimate the extracellular voltage at various locations assuming a perfectly homogeneous, isotropic and purely resistive (0.3 S/m) extracellular space. Specifically, the Neuropixels probe electrode location was adopted from layout specifications. Network simulations were performed at the San Diego supercomputer facility via the NSG (neuroscience gateway) portal. 

## Studies contained 
- `bionet_static`
  - No drift was added. Electrode spacing: 60 channels spaced 20 um vertically and 28 um horizontally. 
  - Four electrode layouts used: two columns (two layouts) and four staggered columns (two layout)

- `bionet_drift`
  - Uniform drift was added by translating 16 micrometers over the duration of the recording (16 minutes).
  - Drift was generated at 0.5 um (32 steps) resolution by interpolating 5 um spaced electrodes with a 2D Gaussian kernel.

- `bionet_shuffle`
  - Random jumping drift was added by dividing the drifting dataset to 32 time segments and shuffling in time.

## References
- [Real-time spike sorting platform for high-density extracellular probes with ground-truth validation and drift correction](https://www.biorxiv.org/content/10.1101/101030v2)
- [BioNet: A Python interface to NEURON for modeling large-scale networks](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0201630)
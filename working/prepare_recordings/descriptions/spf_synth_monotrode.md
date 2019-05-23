---
# This is YAML front matter
label: SYNTH_MONOTRODE
electrode_type: monotrode
doi: 10.1016/j.jneumeth.2012.07.010
ground_truth: simulation
organism: N/A
source: Pedreira C, Martinez J, Ison MJ, Quian Quiroga R
labels:
  - hybrid
---

# SYNTH_MONOTRODE
## Description
*From the author description*:
Simulated dataset used in Pedreira et al., J Neurosci Methods, 2012

This dataset comprises 95 simulations of 10 minutes-long extracellular recordings. Details of the simulation approach can be found in the paper. Simulations included different number of single units, from 2 to 20. For each case, 5 different simulations were performed.

The data associated with each simulation is stored in the variable data located in the file ‘simulation_sim-num.mat’, where sim-num represents the simulation number (from1 to 95). The sampling rate is 24 KHz. 

All the information regarding to the ground truth of the recording is stored in 3 cell arrays located in the file ‘ground_truth.mat’. The details associated to the simulation sim-num are stored in the sim-num-th row of each cell array. Particularly, it includes details of the waveform, class (single unit label or multiunit) and time in the recording, corresponding to each of the spikes included in the simulation.

Variable su_waveforms{sim-num} stores the waveforms of each single unit used in the simulation. Each waveform has 316 points and it is sampled at 96 KHz (the original sampling rate used to create the neural recording before downsampling it to 24Khz).

Variable spike_classes{sim-num} is a vector where the i-th component represents the class associated to the i-th spike in the simulation. It takes values between 0 and tot_SU (the total number of single units included in the simulation, which can be from 2 to 20). Class 0 is associated to the multiunit activity. Each single unit is associated to a waveform stored in su_waveforms{sim-num}.

Variable spike_first_sample{sim-num} is a vector where the i-th component represents the first sample in the recording where the i-th spike in the simulation was inserted (which is associated to the waveform from the class number in the i-th component of spike_classes{sim-num}).

## Recording format
- single channel
- float32 format (1 channel x time order)
- 600s recording duration
- Negative-going polarity (sign was flipped from the original recording supplied by the authors)


## References
- Pedreira C, Martinez J, Ison MJ, Quian Quiroga R. How many neurons can we see with current spike sorting algorithms? J  Neurosci  Methods 211: 58–65, 2012. doi: 10.1016/j.jneumeth.2012.07.010
- [Recordings with ground-truth are available here](https://www135.lamp.le.ac.uk/hgr3/)
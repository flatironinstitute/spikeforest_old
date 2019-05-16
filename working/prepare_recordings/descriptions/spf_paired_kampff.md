---
# This is YAML front matter
label: PAIRED_KAMPFF
electrode_type: silicon-probe
doi:
  - 10.1101/370080
  - 10.1152/jn.00103.2016
ground_truth: intracellular
organism: mouse
source: Adam Kampff lab
labels:
  - in-vivo
---

# PAIRED_KAMPFF

## Paired juxtacellular and silicon probe recording
- Recordings were contributed from Adam [Kampff lab](http://www.kampff-lab.org/validating-electrodes)
- Prepared by J. James Jun, Dec 18, 2018.
- Extracted subarray of 32 channels centered around the activity peak.
- 12 cell pairs were taken from the Neuropixels probe recordings based on the highest SNR.
- Intracellular timing was provided by the Kampff lab.

## Silicon probes used
- `2014_11_25_Pair_3_0`: Neuronexus poly32nn (25 um spacing, staggered three columns)
  - https://drive.google.com/drive/folders/0B6paC2__-QYFNEt6VnZ0QVlkYlk
- `2015_09_03_Pair_9_0A`: IMEC Neuroseeker probe (four columns, 20 um spacing). Subsampled half the electrodes (staggered four columns, neuropixels probe layout)
  - https://drive.google.com/drive/folders/0B6paC2__-QYFTGtfd2NBb1d3ZlE
- `2015_09_03_Pair_9_0B`: IMEC Neuroseeker probe, subsampled the other half of the electrodes
  - https://drive.google.com/drive/folders/0B6paC2__-QYFTGtfd2NBb1d3ZlE
- `c##`: Neuropixels probe (four columns staggered, 20 um vertical spacing, 28 um horizontal spacing). 12 cell pairs available.
  - https://drive.google.com/drive/folders/13GCOuWN4QMW6vQmlNIolUrxPy-4Wv1BC

## References
- https://www.physiology.org/doi/full/10.1152/jn.00103.2016
- https://www.biorxiv.org/content/10.1101/370080v1
---
# This is YAML front matter
label: PAIRED_BOYDEN
electrode_type: silicon-probe
doi: 10.1152/jn.00650.2017
ground_truth: intracellular
organism: mouse
source: Brian D. Allen from Ed Boyden's lab
labels:
  - in-vivo
---

# PAIRED_BOYDEN

This dataset was collected by Brian D. Allen from Ed Boyden's lab. The intracellular and extracellular voltages were recorded simultaneously.
Extracellular voltages were recorded using 128 or 256 site silicon probes custom made at Boyden lab (9x9 um site dimension, 11x11 um site pitch).
128-channel probe has 64x2 site grid pattern and 256-channel probe has 64x4 site grid pattern.
Bad or shorted sites are excluded based on the experimenter's criteria. The number of channels exported excludes the channels from bad sites. 
Bursting spikes (ISI<20ms) are kept up to three successive spikes using the experimeter's burst creteria.

For more info, visit the publication website:
https://www.physiology.org/doi/10.1152/jn.00650.2017
Automated in vivo patch clamp evaluation of extracellular multielectrode array spike recording capability
Brian D. Allen, Caroline Moore-Kochlacs, Jacob Gold Bernstein, Justin Kinney, Jorg Scholvin, Luis Seoane, Chris Chronopoulos, Charlie Lamantia, Suhasa B Kodandaramaiah, Max Tegmark, and Edward S Boyden*

The raw data (.h5 format) was converted to .mda using ironclust v4.0.6 using `irc convert-h5-mda` command.
https://github.com/jamesjun/ironclust

A subset of the data was extracted -- 32 channels near the center of the activity, excluding the bad channels, as documented by the experimenters' annotation.

The recording conditions for each cell are listed below.

```
Neuron  Condition                       Filename        Target Layer    Mean uV (nonburst) on closest electrode Num chans
--------------------------------------------------------------------------------------------------------------------------
419_1   awake natural scene             419_7           V               256
        awake gratings                  419_8           V       257     256
513_2   awake natural scene             513_2_2         V               256
        awake gratings                  513_2_3         V       84      256
513_1   anesth. gratings (50pA stim)    513_1_1         II/III  52      256
        anesth. gratings                513_1_2         II/III          256
531_2   anesth. gratings                531_2_1         V               256
        anesth. natural scene           531_2_2         V       91      256
624_2   anesth. gratings                624_2_1         V               256
        anesth. natural scene           624_2_2         V       53      256
624_5   anesth. gratings                624_5_1         V               256
        anesth. natural scene           624_5_2         V       68      256
509_1   anesth. gratings                509_1_1         II/III          256
        anesth. natural scene           509_1_2         II/III  61      256
1103_1  anesth. gratings                1103_1_1        II/III  70      64
915_8   anesth. gratings                915_8_1         V       101     128
915_10  anesth. gratings                915_10_1        V       83      128
915_17  anesth. gratings                915_17_1        II/III  57      128
915_18  anesth. gratings                915_18_1        II/III  64      128
```

## References
https://www.physiology.org/doi/10.1152/jn.00650.2017

---
title: Edinburgh workshop
date: 2019-06-25
author: Jeremy Magland
---

Today I am introducing SpikeForest at a workshop at University of Edinburgh. The conference is called [*Spike Sorting and Reproducibility for Next Generation Electrophysiology*](http://workshops.inf.ed.ac.uk/ssnge/) and was organized by Matthias Hennig and the SpikeInterface crew. After the presentation I will post the slides here:

[SpikeForest: a web-based spike sorting validation platform and analysis framework](https://docs.google.com/presentation/d/1NWmNT0kfr_dPQqTXHl9azrzS_wHUlQ-GcC_NywxoUMQ/edit?usp=sharing)

Here is the abstract:

> As the collection of automated spike sorting software packages continues to grow, there is much uncertainty and folklore about the quality of their performance in various experimental conditions. Several papers report comparisons on a case-by-case basis, but there is a lack of standardized measures and validation data. Furthermore, there is a potential for bias, such as sub-optimal tuning of competing algorithms, and a focus on one brain region or probe type. Without a fair and transparent comparison, genuine progress in the field remains
difficult.
>  
> We have addressed this challenge by developing SpikeForest, a reproducible, continuously updating platform which benchmarks the performance of spike sorting codes across a large curated database of electrophysiological recordings with ground truth. With contributions from over a dozen participating labs, our database includes hundreds of recordings, in various brain regions, with thousands of ground truth units (and growing). As well as extracellular
recordings with paired intracellular ground truth, we include state-of-the-art simulated recordings, and hybrid synthetic datasets.
>  
> In collaboration with the SpikeInterface project, we have wrapped many popular sorting algorithms (including HerdingSpikes2, IronClust, JRCLUST, KiloSort, Kilosort2, Klusta, MountainSort4, SpyKING CIRCUS, Tridesclous, and YASS) under a common Python interface that performs automatic caching of results and guarantees reproducibility via singularity containers and transparency of parameter choices. This also enables researchers themselves to install and run all tested sorters with a single interface.
>  
> The large scale of our analysis demands an automatically updating nightly batch on a high performance compute cluster, where hundreds of sorting jobs are run in parallel (> 20000 CPU/GPU hours). Results are uploaded to a MongoDB database which is then accessed by our public-facing web site. This site allows intuitive comparison of metrics (precision, recall, overall accuracy, and runtime) across all sorters and recordings, and interactive visual “drilling down” into each sorting output at the single unit or event channel-trace level. The web technology is built on Node.js/React.
>  
> In cooperation with SpikeInterface, the SpikeForest framework will continuously validate community progress in automated spike sorting, and guide neuroscientists to an optimal choice of sorter and parameters for a wide range of probes and brain regions.
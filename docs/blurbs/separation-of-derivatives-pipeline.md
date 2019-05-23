## Separation of derivatives pipeline

23 May 2019

Here I describe some developments on the SpikeForest analysis and the rationale
behind the changes. These changes aim to improve the modularity, stability, and
maintainability of the analysis system.

The main analysis script runs all the sorting algorithms on all of the
recordings on a daily basis. If nothing has changed, it should only take only a
few minutes to traverse through all of the jobs and determine that no updates
are needed. The output of this pipeline is intentionally limited to (1) the
firings.mda file for each sorting result, (2) information about the ground truth
units, and (3) information about the comparison with ground truth.

Additional "derivative" data, such as spike sprays, must also be assembled for
every recording. Depending on the number of ground truth units and other
factors, this part of the analysis (which we expect to expand over time) may
actually take longer than the spike sorting. The bookkeeping effort of this step
also adds complexity to the overall analysis. Furthermore, as the number and
complexity of such derivatives increases over time, the burden on keeping the
analysis code, website database, and database code all synchronized will
increase in complexity.

To remedy these issues, I have taken steps to decouple the main spike sorting
processing pipeline and the website database from the generation of these
derivatives as explained below.

The main spike sorting proceeds as follows:

* Prepare recordings and upload data to pairio/kachery
* Configure analysis (sorting parameters, etc.) in analysis.*.json files
* Run all spike sorters are all recordings with MountainTools caching and store
  results in pairio/kachery
* Compare with ground truth and store results in pairio/kachery
* Populate website database with results

The generation of derivatives pipeline is independent (only loosely connected)
and comprises the following steps:

* Retrieve spike sorting results from pairio/kachery
* Generate derivatives (e.g., spike sprays) with MountainTools caching and
  upload results to pairio/kachery
* Note: data are *not* uploaded to the website database

The website then retrieves the derivatives directly from pairio/kachery. If a
particular derivative has not yet been calculated, the website simply displays a
"not found" message. This allows the website to be continuously updated with new
results even when derivative generation scripts lag behind.

A crucial aspect of the system is that derivatives are stored in pairio/kachery
according to the hash of their inputs rather than by the names of the recording
and spike sorter. This is critical for ensuring that the correct derivative
objects are always displayed and that derivatives never need to be redundantly
recomputed. For example, here is code used by the website to retrieve spike
spray data for a particular recording / sorter / unit ID:

```
let key0 = {
    "name": "unit-details-v0.1.0",
    "recording_directory": sr.recordingDirectory,
    "firings_true": sr.firingsTrue,
    "firings": sr.firings
};
let obj = await this.loadObject(null, {collection:'spikeforest', key:key0});
```

The recording directory in this case would be something like

```sha1dir://fb52d510d2543634e247e0d2d1d4390be9ed9e20.synth_magland/datasets_noise10_K10_C4/001_synth```

and similarly the other inputs (firings and firings_true) are addressed by their
content hashes.

Another advantage to this system is that the procedure for generating the
derivatives may be split into several independently running scripts. Thus the
overall pipeline consists of a collection of independent, loosely connected
components, which improves the modularity, stability, and maintainability of the
analysis procedure.
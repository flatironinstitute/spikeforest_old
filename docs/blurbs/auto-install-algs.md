## Auto installation of sorting algorithms

20 May 2019

The MATLAB sorting algorithms are not as rigorously repeatable since they do not utilize singularity containers. To remedy this, I am building in auto-install scripts for these processors. For IronClust, the install script just clones the IronClust repo at a particular commit. For KiloSort and Kilosort2, a GPU/CUDA compilation step is also part of the auto-install.

Thus far I have implemented this auto-installer for the following algs:

* IronClust

* Kilosort2

The following environment variables will no longer have an effect: `IRONCLUST_PATH`, `KILOSORT2_PATH`

For development and testing purposes, if you want to use the old method (not auto installing) you can set the following environment variables instead: `IRONCLUST_PATH_DEV`, `KILOSORT2_PATH_DEV`

Otherwise, the source code for these projects will (by default) automatically be cloned to `~/spikeforest_algs/`

For example, 

```
~/spikeforest_algs/ironclust_042b600b014de13f6d11d3b4e50e849caafb4709
```

The wrappers include hard-coded commits for the repos.

In this way, it is possible to update the commit (e.g., bug fix) without incrementing the wrapper version.


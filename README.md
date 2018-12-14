## SpikeForest2

This is a meta repository that is meant to be used in development/editable mode. To install, you can do the following in a fresh conda environment:

```
./install_conda.sh
```

This will install snapshots of various python packages (including vdomr, spikeextractors, spikewidgets, mlprocessors, etc.), so you should make sure these don't conflict with existing packages on your system.

This project contains a snapshot of a number of different dependent projects contained in repo/. These may or may not be up-to-date with the associated stand-alone packages. In this way, spikeforest2 is a snapshot project that contains all the necessary code, and is less susceptible to breaking changes in other packages.


## SpikeForest2

This is a meta repository that is meant to be used in development/editable mode. To install using conda, first create a conda environment with python 3.6:

```
conda create -n spikeforest2 python=3.6
conda activate spikeforest2
```

Then run the install script

```
./install_within_conda.sh
```

In addition, if you want to use some of the interactive graphics within jupyterlab, do the following:

```
./install_jp_proxy_widget.sh
```

To run colab jupyter notebooks in a local runtime, we recommend chrome browser or chromium-browser. Firefox browser may not connect to the local runtime environment.

This project contains a snapshot of a number of different dependent projects contained in repo/. These may or may not be up-to-date with the associated stand-alone packages. In this way, spikeforest2 is a snapshot project that contains all the necessary code, and is less susceptible to breaking changes in other packages.

Further documentation: [spikeforest-docs](https://github.com/flatironinstitute/spikeforest-docs/blob/master/docs/index.md)


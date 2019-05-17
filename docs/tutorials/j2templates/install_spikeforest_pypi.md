The first step is to install spikeforest and mountaintools. The easiest way is to use
the PyPI packages as follows.

```
{% include './j2templates/install_spikeforest_pypi.sh' %}
```

To use the containerized versions of the spike sorters (recommended), you should
[install
singularity](https://www.sylabs.io/guides/3.0/user-guide/quick_start.html#quick-installation-steps).
This will work for all of the non-Matlab spike sorters (in the future we will
also containerize the Matlab packages).
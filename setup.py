import setuptools

pkg_name = "spikeforest2"

setuptools.setup(
    name=pkg_name,
    version="0.1.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Spike sorting validation and comparison system",
    url="https://github.com/magland/spikeforest2",
    packages=[
        'vdomr',
        'spikeforest_batch_run',
        'spikeextractors','spikewidgets','spiketoolkit',
        'mlprocessors',
        'kbucket','pairio',
        'spikeforest',
        'batcho',
        'spikeforestwidgets',
        'ml_ms4alg'
    ],
    install_requires=[
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

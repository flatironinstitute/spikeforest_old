import setuptools

pkg_name = "spikeforest2"

# NOTE: you should install this project in development mode
# > python setup.py develop

setuptools.setup(
    name=pkg_name,
    version="0.2.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Spike sorting validation and comparison system",
    url="https://github.com/flatironinstitute/spikeforest2",
    packages=[
        'spikeextractors', 'spikewidgets', 'spiketoolkit',
        'spikeforest','spikeforest_analysis'
    ],
    install_requires=[
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

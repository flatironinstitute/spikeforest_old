import setuptools

pkg_name = "spikeforest"

# NOTE: you should install this project in development mode
# > python setup.py develop

setuptools.setup(
    name=pkg_name,
    version="0.6.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Spike sorting",
    packages=setuptools.find_packages(),
    package_dir={
        'spikesorters': 'spikesorters',
        'spikeforestwidgets': 'spikeforestwidgets',
        'forestview': 'forestview'
    },
    include_package_data=True,
    install_requires=[
        'numpy', 'scipy', 'matplotlib', 'requests', 'pillow', 'pandas', 'ipython', 'h5py', 'setuptools-git', 'scikit-learn', 'python-frontmatter', 'spikeextractors>=0.4.2,<0.5'
    ],
    scripts=['bin/forestview'],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

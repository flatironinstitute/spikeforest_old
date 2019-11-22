import setuptools

pkg_name = "spikeforest_container_utils"

setuptools.setup(
    name=pkg_name,
    version="0.1.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Utilities for spikeforest containers",
    packages=setuptools.find_packages(),
    scripts=[
    ],
    install_requires=[],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

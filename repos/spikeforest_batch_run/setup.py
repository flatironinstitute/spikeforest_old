import setuptools

pkg_name="spikeforest_batch_run"

setuptools.setup(
    name=pkg_name,
    version="0.1.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="",
    url="https://github.com/magland/spikeforest_batch_run",
    packages=setuptools.find_packages(),
    install_requires=[
        'kbucket'
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

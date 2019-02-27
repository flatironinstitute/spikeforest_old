import setuptools

pkg_name = "mountaintools"

# NOTE: you should install this project in development mode
# > python setup.py develop

setuptools.setup(
    name=pkg_name,
    version="0.1.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Spike sorting",
    packages=setuptools.find_packages(),
    install_requires=[
        'numpy','matplotlib','requests','pillow','pandas','ipython','h5py'
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

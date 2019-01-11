import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

pkgs = setuptools.find_packages()
print('found these packages:', pkgs)

pkg_name="ml_ms4alg"

setuptools.setup(
    name=pkg_name,
    version="0.2.1",
    author="Jeremy Magland",
    author_email="",
    description="Mountainsort v4 for MountainLab",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/magland/ml_ms4alg",
    packages=pkgs,
    package_data={
        '': ['*.mp'], # Include all processor files
    },
    install_requires=
    [
        'pybind11',
        'isosplit5',
        'numpy',
        'mountainlab_pytools',
        'h5py',
        'spikeextractors',
        'sklearn'
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    conda={
        "build_number":0,
        "build_script":[
            "python -m pip install .",
            "CMD=\"ln -sf $SP_DIR/"+pkg_name+" `CONDA_PREFIX=$PREFIX ml-config package_directory`/"+pkg_name+"\"",
            "echo $CMD",
            "$CMD"
        ],
        "test_commands":[
            "ml-list-processors",
            "ml-spec ms4alg.sort"
        ],
        "test_imports":[
        ],
        "requirements":[
            "python",
            "pip",
            "pybind11",
            "isosplit5",
            "numpy",
            "mountainlab",
            "mountainlab_pytools",
            "h5py",
            "sklearn"
        ]
    }
)

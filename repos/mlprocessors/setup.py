import setuptools

pkg_name="mlprocessors"

setuptools.setup(
    name=pkg_name,
    version="0.3.0",
    author="Witold Wysota and Jeremy Magland",
    author_email="wysota@wysota.org",
    description="A Python framework for making MountainLab processor packages",
    url="https://github.com/flatironinstitute/mlprocessors",
    packages=setuptools.find_packages(),
    package_data={
        '': [ ]
    },
    install_requires=[
        'argparse',
        'pairio',
        'kbucket'
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
            "echo $CMD",
            "$CMD"
        ],
        "test_commands":[
        ],
        "test_imports":[
            "mlprocessors",
            "mlprocessors.core",
            "mlprocessors.registry",
            "mlprocessors.validators"
        ],
        "requirements":[
            "python",
            "pip",
        ]
    }
)

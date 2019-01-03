import setuptools

pkg_name="spikeforestwidgets"

setuptools.setup(
    name=pkg_name,
    version="0.2.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="",
    url="https://github.com/magland/spikeforestwidgets",
    packages=setuptools.find_packages(),
    package_data={
        '': ['dist/*']
    },
    install_requires=[],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ),
    conda={
        "build_number":0,
        "build_script":[
            "python -m pip install jp_proxy_widget",
            "python -m pip install --no-deps --ignore-installed .",
            "echo $CMD",
            "$CMD"
        ],
        "test_commands":[
        ],
        "test_imports":[
        ],
        "requirements":[
            "python",
            "pip",
            "ipywidgets"
        ]
    }
)

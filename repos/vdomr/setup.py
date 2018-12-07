import setuptools

pkg_name = "vdomr"

setuptools.setup(
    name=pkg_name,
    version="0.2.2",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Interactive DOM components for python and jupyter",
    url="https://github.com/magland/vdomr",
    packages=setuptools.find_packages(),
    install_requires=[
        'ipython'
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

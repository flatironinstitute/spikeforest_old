import setuptools

pkg_name="cairio"

setuptools.setup(
    name=pkg_name,
    version="0.1.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Python interface to cairio",
    packages=setuptools.find_packages(),
    package_data={},
    install_requires=[
        "fasteners"
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

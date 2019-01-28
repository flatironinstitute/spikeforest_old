import setuptools

pkg_name="kbucket"

setuptools.setup(
    name=pkg_name,
    version="0.13.0",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Python client for kbucket",
    url="https://github.com/flatironinstitute/kbucket",
    packages=setuptools.find_packages(),
    package_data={},
    install_requires=[
        "requests",
        "pairio"
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

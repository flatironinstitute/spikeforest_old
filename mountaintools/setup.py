import setuptools

pkg_name = "mountaintools"

# NOTE: you should install this project in development mode
# > python setup.py develop

setuptools.setup(
    name=pkg_name,
    version="0.2.9",
    author="Jeremy Magland",
    author_email="jmagland@flatironinstitute.org",
    description="Tools for reproducible scientific research",
    packages=setuptools.find_packages(),
    scripts=['bin/kb-cat', 'bin/kb-ls', 'bin/kb-download', 'bin/kb-snapshot', 'bin/kb-resolve-key-path', 'bin/kb-find'],
    install_requires=[
        'matplotlib','requests','ipython','simple-crypt','python-dotenv'
        #        'matplotlib','requests','ipython','simple-crypt','python-dotenv', 'asyncio', 'nest_asyncio', 'aiohttp'
    ],
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    )
)

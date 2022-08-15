#!/usr/bin/env python3
from setuptools import setup, find_packages

from nldiff import __version__

requirements = open("requirements.txt").read().strip().split("\n")

setup(
    name="nldiff",
    packages=find_packages(),
    version=__version__,
    description="Netlist Diff Tool",
    long_description=open("Readme.md").read(),
    long_description_content_type="text/markdown",
    author="Mohamed Gaber",
    author_email="donn@efabless.com",
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Intended Audience :: Developers",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
    ],
    entry_points={"console_scripts": ["nldiff = nldiff.__main__:diff_cmd"]},
    python_requires=">3.6",
)

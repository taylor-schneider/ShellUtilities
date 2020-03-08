#!/usr/bin/python

import setuptools

# Specify the relative directory where the source code is being stored
# This is the root directory for the namespaces, packages, modules, etc.
source_code_dir = "src"

with open('README.md', "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="ShellUtilities",
    version="1.0.0",
    author="tschneider",
    author_email="tschneider@live.com",
    description="A library for interacting with the shell.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(source_code_dir),
    package_dir={
        "": source_code_dir
    },
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
	    "Operating System :: OS Independent"
    ]
)





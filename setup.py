#!/usr/bin/env python
# -*- coding: utf-8 -*-

# setup.py
"""
A setuptools setup file for IQDM Analytics
"""
# Copyright (c) 2021 Dan Cutright
# This file is part of IQDM Analytics, released under a MIT license.
#    See the file LICENSE included with this distribution, also
#    available at https://github.com/cutright/DVH-Analytics

import os
from setuptools import setup, find_packages
from iqdma._version import __version__


if os.environ.get("READTHEDOCS") == "True":
    requirements_path = "docs/requirements.txt"
else:
    requirements_path = "requirements.txt"

with open(requirements_path, "r") as doc:
    requires = [line.strip() for line in doc]

with open("README.rst", "r") as doc:
    long_description = doc.read()


setup(
    name="iqdma",
    include_package_data=True,
    python_requires=">3.5",
    packages=find_packages(),
    version=__version__,
    description="Analyze IMRT QA Report data mined with IQDM-PDF",
    author="Dan Cutright",
    author_email="dan.cutright@gmail.com",
    url="https://github.com/IQDM/IQDM-Analytics",
    download_url="https://github.com/IQDM/IQDM-Analytics/archive/master.zip",
    license="MIT License",
    keywords=[
        "radiation therapy",
        "research",
        "IMRT QA",
        "bokeh",
        "analytics",
        "wxpython",
    ],
    classifiers=[],
    install_requires=requires,
    entry_points={"console_scripts": ["iqdma = iqdma.main:start"]},
    long_description=long_description,
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import versioneer

setup(
    name='pert_belly_hack_backend',
    author="doubleO8",
    author_email="wb008@hdm-stuttgart.de",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="no description",
    long_description="no long description either",
    url="https://doubleo8.github.io/e2openplugin-OpenWebif/",
    packages=['pert_belly_hack_backend'],
)

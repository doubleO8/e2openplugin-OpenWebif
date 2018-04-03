#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import versioneer

setup(
    name='pert_belly_hack',
    author="doubleO8",
    author_email="wb008@hdm-stuttgart.de",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='Packaging helper for preparing the contents of an OPKG file '
                'containing a web interface for enigma2 devices.',
    long_description="no long description.",
    url="https://doubleo8.github.io/e2openplugin-OpenWebif/",
    packages=['pert_belly_hack'],
    package_data={
        'pert_belly_hack': ['templates/*']
    }
)

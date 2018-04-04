#!/usr/bin/env python
# -*- coding: utf-8 -*-
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import versioneer

DESCRIPTION = 'Packaging helper for preparing the contents of an OPKG file ' \
              'containing a web interface for enigma2 devices.' \
              'Also generates contents for github pages.'

setup(
    name='pert_belly_hack',
    author="doubleO8",
    author_email="wb008@hdm-stuttgart.de",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    url="https://doubleo8.github.io/e2openplugin-OpenWebif/",
    packages=['pert_belly_hack'],
    package_data={
        'pert_belly_hack': ['templates/*']
    },
    scripts=[
        "pbh-harvest",
        "pbh-prepare",
    ]
)

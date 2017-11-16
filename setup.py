#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import versioneer

setup(
    name='beppo',
    author="nobody",
    author_email="nobody@localhost",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description='no description',
    long_description="no long description either",
    url="http://example.com",
    packages=['beppo'],
)

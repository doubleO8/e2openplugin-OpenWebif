#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI tool: generate OPKG package and meta data.
"""
import pprint

import pert_belly_hack
from pert_belly_hack.packaging import AlPackino

from pert_belly_hack_backend.defaults import PACKAGE_META

if __name__ == '__main__':
    print("Pert Belly Hack {:s}: {:s}".format(
        pert_belly_hack.__version__, 'PREPARE'))
    pprint.pprint(PACKAGE_META)

    AL = AlPackino(package_meta=PACKAGE_META)
    AL.prepare()

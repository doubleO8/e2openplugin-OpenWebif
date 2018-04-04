#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI tool: generate github pages contents.
"""
import pprint
import pert_belly_hack
from pert_belly_hack.harvesting import HarvestKeitel

from pert_belly_hack_backend.defaults import PACKAGE_META

if __name__ == '__main__':
    print("Pert Belly Hack {:s}: {:s}".format(
        pert_belly_hack.__version__, 'HARVEST'))
    pprint.pprint(PACKAGE_META)

    HARVEY = HarvestKeitel(package_meta=PACKAGE_META)
    HARVEY.harvest()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from . import __version__

#: meta data for opkg
PACKAGE_META = {
    "package": "enigma2-plugin-extensions-openwebif",
    "upstream_version": __version__,
    "epoch": 1,
}

#: path for github-pages
OUTPUT_PATH = 'pages_out'

#: path for package contents
PACKAGE_OUTPUT_PATH = 'pack'

#: relative path on enigma2 device
TARGET_PATH_REL = 'usr/lib/enigma2/python/Plugins/Extensions/OpenWebif'

#: relative path to be used for the 'latest opk' symlink
LATEST_OPK_PATH_REL = 'latest.opk'

#: relative path of build tag information file
TAG_PATH_REL = "public/tag.json"

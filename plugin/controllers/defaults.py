#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

PLUGIN_ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
PUBLIC_PATH = PLUGIN_ROOT_PATH + '/public'
VIEWS_PATH = PLUGIN_ROOT_PATH + '/controllers/views'

#: paths where folders containing picons could be located
PICON_PREFIXES = (
    "/usr/share/enigma2/",
    "/media/hdd/",
    "/",
    "/media/cf/",
    "/media/mmc/",
    "/media/usb/",
)

#: subfolders containing picons
PICON_FOLDERS = ('picon', 'owipicon',)

#: extension of picon files
PICON_EXT = ".png"


def detect_picon_path():
    for prefix in PICON_PREFIXES:
        if not os.path.isdir(prefix):
            continue

        for folder in PICON_FOLDERS:
            current = prefix + folder + '/'
            if not os.path.isdir(current):
                continue

            for item in os.listdir(current):
                if os.path.isfile(current + item) and item.endswith(PICON_EXT):
                    return current

    return None

PICON_PATH = detect_picon_path()

THEMES = [
    'original-small-screen',
    'original-small-screen',
    'original-small-screen :)'
]

FILE_ACCESS_WHITELIST = [
    '/etc/enigma2/lamedb',
    '/var/etc/satellites.xml'
]
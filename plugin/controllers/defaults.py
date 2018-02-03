#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

PLUGIN_NAME = 'OpenWebif'
PLUGIN_DESCRIPTION = "OpenWebif Configuration"
PLUGIN_WINDOW_TITLE = PLUGIN_DESCRIPTION
LOG_FILES_ROOT = '/media/hdd/'

PLUGIN_ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
PUBLIC_PATH = PLUGIN_ROOT_PATH + '/public'
VIEWS_PATH = PLUGIN_ROOT_PATH + '/controllers/views'
FAVICON_PATH = PUBLIC_PATH + '/images/favicon.png'

PLUGIN_ICON_HD = './public/plugin_icon_hd.png'
PLUGIN_ICON = './public/plugin_icon.png'

sys.path.insert(0, PLUGIN_ROOT_PATH)

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
    '/var/etc/satellites.xml',
    '/etc/tuxbox/satellites.xml',
]

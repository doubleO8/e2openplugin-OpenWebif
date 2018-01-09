# -*- coding: utf-8 -*-
import os
import gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PluginLanguageDomain = "OpenWebif"
PluginLanguagePath = "Extensions/OpenWebif/locale"

PLUGIN_ROOT_PATH = os.path.dirname(__file__)
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


def _detect_picon_path():
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


def _locale_init():
    gettext.bindtextdomain(
        PluginLanguageDomain,
        resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


def _(txt):
    t = gettext.dgettext(PluginLanguageDomain, txt)
    if t == txt:
        t = gettext.gettext(txt)
    return t


_locale_init()
language.addCallback(_locale_init)
PICON_PATH = _detect_picon_path()

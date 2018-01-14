# -*- coding: utf-8 -*-
import gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

from controllers.defaults import detect_picon_path

PluginLanguageDomain = "OpenWebif"
PluginLanguagePath = "Extensions/OpenWebif/locale"


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


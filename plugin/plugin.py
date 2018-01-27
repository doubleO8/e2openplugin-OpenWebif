# -*- coding: utf-8 -*-

##############################################################################
#                         <<< OpenWebif >>>                                  #
#                                                                            #
#                        2011 E2OpenPlugins                                  #
#                                                                            #
#  This file is open source software; you can redistribute it and/or modify  #
#     it under the terms of the GNU General Public License version 2 as      #
#               published by the Free Software Foundation.                   #
#                                                                            #
##############################################################################
#
#
#
# Authors: meo <lupomeo@hotmail.com>, skaman <sandro@skanetwork.com>
# Graphics: .....
import os
import logging

from controllers.defaults import THEMES, LOG_FILES_ROOT, PLUGIN_WINDOW_TITLE
from controllers.defaults import PLUGIN_NAME, PLUGIN_DESCRIPTION
from controllers.defaults import PLUGIN_ICON, PLUGIN_ICON_HD

log_args = dict(
    level=logging.INFO,
    format='%(asctime)s %(name)-60s %(levelname)-8s '
           '%(funcName)-32s (#%(lineno)04d): %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)

if os.path.isdir(LOG_FILES_ROOT):
    log_args['filename'] = "{:s}/{:s}.log".format(LOG_FILES_ROOT,
                                                  PLUGIN_NAME.lower())

logging.basicConfig(**log_args)

from Screens.Screen import Screen  # noqa: E402
from Plugins.Plugin import PluginDescriptor  # noqa: E402
from Components.ActionMap import ActionMap  # noqa: E402
from Components.Label import Label  # noqa: E402
from Components.ConfigList import ConfigListScreen  # noqa: E402
from Components.config import config, getConfigListEntry  # noqa: E402
from Components.config import ConfigSubsection, ConfigSelection  # noqa: E402
from Components.config import ConfigInteger, ConfigYesNo, ConfigText  # noqa: E402,E501
from enigma import getDesktop  # noqa: E402

from controllers.models.info import getInfo  # noqa: E402
from httpserver import HttpdStart, HttpdStop, HttpdRestart  # noqa: E402
from controllers.i18n import _  # noqa: E402


LOG = logging.getLogger(__name__)

config.OpenWebif = ConfigSubsection()
config.OpenWebif.enabled = ConfigYesNo(default=True)
config.OpenWebif.identifier = ConfigYesNo(default=True)
config.OpenWebif.identifier_custom = ConfigYesNo(default=False)
config.OpenWebif.identifier_text = ConfigText(default="", fixed_size=False)
config.OpenWebif.port = ConfigInteger(default=80, limits=(1, 65535))
config.OpenWebif.streamport = ConfigInteger(default=8001, limits=(1, 65535))
config.OpenWebif.webcache = ConfigSubsection()
# FIXME: anything better than a ConfigText?
config.OpenWebif.webcache.collapsedmenus = ConfigText(
    default="", fixed_size=False)
config.OpenWebif.webcache.zapstream = ConfigYesNo(default=False)
config.OpenWebif.webcache.theme = ConfigSelection(
    default='original-small-screen', choices=THEMES)
config.OpenWebif.webcache.moviesort = ConfigSelection(
    default='name', choices=['name', 'named', 'date', 'dated'])
config.OpenWebif.webcache.showchannelpicon = ConfigYesNo(default=True)
config.OpenWebif.webcache.mepgmode = ConfigInteger(default=1, limits=(1, 2))

# Use service name for stream
config.OpenWebif.service_name_for_stream = ConfigYesNo(default=True)

# encoding of EPG data
config.OpenWebif.epg_encoding = ConfigSelection(
    default='utf-8',
    choices=[
        'utf-8',
        'iso-8859-15',
        'iso-8859-1',
        'iso-8859-2',
        'iso-8859-3',
        'iso-8859-4',
        'iso-8859-5',
        'iso-8859-6',
        'iso-8859-7',
        'iso-8859-8',
        'iso-8859-9',
        'iso-8859-10',
        'iso-8859-16'])

try:
    imagedistro = getInfo()['imagedistro']
except (KeyError, TypeError):
    imagedistro = "unknown"

CONFIG_SCREEN_XML = """
    <screen position="center,center" size="700,340"
        title="OpenWebif Configuration">
        <widget name="lab1" position="10,30" halign="center" size="680,60"
            zPosition="1" font="Regular;24" valign="top" transparent="1" />
        <widget name="config" position="10,100" size="680,180"
            scrollbarMode="showOnDemand" />
        <ePixmap position="140,290" size="140,40"
            pixmap="skin_default/buttons/red.png" alphatest="on" />
        <widget name="key_red" position="140,290" zPosition="1" size="140,40"
            font="Regular;20" halign="center" valign="center"
            backgroundColor="red" transparent="1" />
        <ePixmap position="420,290" size="140,40"
            pixmap="skin_default/buttons/green.png" alphatest="on"
            zPosition="1" />
        <widget name="key_green" position="420,290" zPosition="2"
            size="140,40" font="Regular;20" halign="center" valign="center"
            backgroundColor="green" transparent="1" />
    </screen>
"""


class OpenWebifConfig(Screen, ConfigListScreen):
    """
    Enigma2 plugin configuration screen.
    """

    def __init__(self, session):
        self.skin = CONFIG_SCREEN_XML
        Screen.__init__(self, session)

        self.list = []
        ConfigListScreen.__init__(self, self.list)
        self["key_red"] = Label(_("Cancel"))
        self["key_green"] = Label(_("Save"))
        self["lab1"] = Label(_("OpenWebif url: http://yourip:port"))

        self["actions"] = ActionMap(["WizardActions", "ColorActions"],
                                    {
                                        "red": self.keyCancel,
                                        "back": self.keyCancel,
                                        "green": self.keySave,

                                    }, -2)
        self.runSetup()
        self.onLayoutFinish.append(self.setWindowTitle)

    def runSetup(self):
        self.list = []
        self.list.append(
            getConfigListEntry(
                _("OpenWebInterface Enabled"),
                config.OpenWebif.enabled))

        if config.OpenWebif.enabled.value:
            self.list.append(
                getConfigListEntry(
                    _("Show box name in header"),
                    config.OpenWebif.identifier))

            if config.OpenWebif.identifier.value:
                self.list.append(
                    getConfigListEntry(
                        _("Use custom box name"),
                        config.OpenWebif.identifier_custom))
                if config.OpenWebif.identifier_custom.value:
                    self.list.append(
                        getConfigListEntry(
                            _("Custom box name"),
                            config.OpenWebif.identifier_text))
            self.list.append(
                getConfigListEntry(
                    _("HTTP port"),
                    config.OpenWebif.port))
            self.list.append(
                getConfigListEntry(
                    _("Add service name to stream information"),
                    config.OpenWebif.service_name_for_stream))

            if imagedistro in ("VTi-Team Image",):
                self.list.append(
                    getConfigListEntry(
                        _("Character encoding for EPG data"),
                        config.OpenWebif.epg_encoding))

        self["config"].list = self.list
        self["config"].l.setList(self.list)

    def setWindowTitle(self):
        self.setTitle(_(PLUGIN_WINDOW_TITLE))

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.runSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.runSetup()

    def keySave(self):
        for x in self["config"].list:
            x[1].save()

        if config.OpenWebif.enabled.value:
            HttpdRestart(global_session)
        else:
            HttpdStop(global_session)
        self.close()

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()


def on_configure_plugin(session, **kwargs):
    """
    Plugin configured(?) callback function.

    Args:
        session: (?) Session instance
    """
    LOG.info("on_configure_plugin({!r}, {!r})".format(session, kwargs))
    # LOG.debug(dir(session))
    # ['__doc__', '__init__', '__module__', 'close', 'create',
    #  'current_dialog', 'delay_timer', 'deleteDialog', 'desktop',
    #  'dialog_stack', 'doInstantiateDialog', 'execBegin', 'execDialog',
    #  'execEnd', 'in_exec', 'instantiateDialog', 'instantiateSummaryDialog',
    #  'nav', 'open', 'openWithCallback', 'popCurrent', 'popSummary',
    #  'processDelay', 'pushCurrent', 'pushSummary', 'screen', 'summary',
    #  'summary_desktop', 'summary_stack']
    session.open(OpenWebifConfig)


def on_network_configuration_read(reason, **kwargs):
    """
    Network interface callback function.

    Args:
        reason: Reason
    """
    LOG.info("on_network_configuration_read({!r}, {!r})".format(
        reason, kwargs))

    try:
        if reason is True:
            HttpdStart(global_session)
        else:
            HttpdStop(global_session)
    except Exception as exc:
        LOG.error(exc)


def on_start_session(reason, session):
    """
    Start Session callback function.

    Args:
        reason: Reason
        session: (?) Session instance
    """
    LOG.info("on_start_session({!r}, {!r})".format(reason, session))
    # LOG.debug(dir(session))
    global global_session
    global_session = session


def on_main_menu(menuid, **kwargs):
    LOG.info("on_main_menu({!r}, {!r})".format(menuid, kwargs))
    if menuid == "network":
        return [(PLUGIN_NAME, on_configure_plugin, PLUGIN_NAME.lower(), 45)]
    else:
        return []


def Plugins(**kwargs):
    """
    Plugin loader(?)
    """
    result = [
        PluginDescriptor(
            where=[PluginDescriptor.WHERE_SESSIONSTART],
            fnc=on_start_session),
        PluginDescriptor(
            where=[PluginDescriptor.WHERE_NETWORKCONFIG_READ],
            fnc=on_network_configuration_read),
    ]
    screenwidth = getDesktop(0).size().width()

    if imagedistro == "openatv":
        result.append(
            PluginDescriptor(
                name=PLUGIN_NAME,
                description=_(PLUGIN_DESCRIPTION),
                where=PluginDescriptor.WHERE_MENU,
                fnc=on_main_menu))

    if screenwidth and screenwidth >= 1920:
        result.append(
            PluginDescriptor(
                name=PLUGIN_NAME,
                description=_(PLUGIN_DESCRIPTION),
                icon=PLUGIN_ICON_HD,
                where=[PluginDescriptor.WHERE_PLUGINMENU],
                fnc=on_configure_plugin))
    else:
        result.append(
            PluginDescriptor(
                name=PLUGIN_NAME,
                description=_(PLUGIN_DESCRIPTION),
                icon=PLUGIN_ICON,
                where=[PluginDescriptor.WHERE_PLUGINMENU],
                fnc=on_configure_plugin))

    return result

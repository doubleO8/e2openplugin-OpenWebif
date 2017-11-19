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
import logging

from Screens.Screen import Screen
from Plugins.Plugin import PluginDescriptor
from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.ConfigList import ConfigListScreen
from Components.config import config, getConfigListEntry, ConfigSubsection, \
    ConfigInteger, ConfigYesNo, ConfigText, ConfigSelection
from enigma import getDesktop
from controllers.models.info import getInfo

from httpserver import HttpdStart, HttpdStop, HttpdRestart

from __init__ import _

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-8s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filename="/media/hdd/openwebif.log")

LOG = logging.getLogger("PLUGIN")

# not used redmond -> original , trontastic , ui-lightness
THEMES = [
    'original',
    'base',
    'black-tie',
    'blitzer',
    'clear',
    'cupertino',
    'dark-hive',
    'dot-luv',
    'eggplant',
    'excite-bike',
    'flick',
    'hot-sneaks',
    'humanity',
    'le-frog',
    'mint-choc',
    'overcast',
    'pepper-grinder',
    'smoothness',
    'south-street',
    'start',
    'sunny',
    'swanky-purse',
    'ui-darkness',
    'vader',
    'original-small-screen']

PLUGIN_NAME = 'OpenWebif'
PLUGIN_ICON_HD = 'openwebifhd.png'
PLUGIN_ICON = 'openwebif.png'

config.OpenWebif = ConfigSubsection()
config.OpenWebif.enabled = ConfigYesNo(default=True)
config.OpenWebif.identifier = ConfigYesNo(default=True)
config.OpenWebif.identifier_custom = ConfigYesNo(default=False)
config.OpenWebif.identifier_text = ConfigText(default="", fixed_size=False)
config.OpenWebif.port = ConfigInteger(default=80, limits=(1, 65535))
config.OpenWebif.streamport = ConfigInteger(default=8001, limits=(1, 65535))
config.OpenWebif.auth = ConfigYesNo(default=False)
config.OpenWebif.xbmcservices = ConfigYesNo(default=False)
config.OpenWebif.webcache = ConfigSubsection()
# FIXME: anything better than a ConfigText?
config.OpenWebif.webcache.collapsedmenus = ConfigText(
    default="", fixed_size=False)
config.OpenWebif.webcache.zapstream = ConfigYesNo(default=False)
config.OpenWebif.webcache.theme = ConfigSelection(
    default='original', choices=THEMES)
config.OpenWebif.webcache.moviesort = ConfigSelection(
    default='name', choices=['name', 'named', 'date', 'dated'])
config.OpenWebif.webcache.showchannelpicon = ConfigYesNo(default=True)
config.OpenWebif.webcache.mepgmode = ConfigInteger(default=1, limits=(1, 2))

# Use service name for stream
config.OpenWebif.service_name_for_stream = ConfigYesNo(default=True)
# authentication for streaming
config.OpenWebif.auth_for_streaming = ConfigYesNo(default=False)
config.OpenWebif.no_root_access = ConfigYesNo(default=False)
config.OpenWebif.local_access_only = ConfigSelection(
    default=' ', choices=[' '])
config.OpenWebif.vpn_access = ConfigYesNo(default=False)
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

imagedistro = getInfo()['imagedistro']

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
                    _("Enable HTTP Authentication"),
                    config.OpenWebif.auth))
            if config.OpenWebif.auth.value:
                self.list.append(
                    getConfigListEntry(
                        _("Enable Authentication for streaming"),
                        config.OpenWebif.auth_for_streaming))
                self.list.append(
                    getConfigListEntry(
                        _("Disable remote access for user root"),
                        config.OpenWebif.no_root_access))
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
        self.setTitle(_("OpenWebif Configuration"))

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.runSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.runSetup()

    def keySave(self):
        for x in self["config"].list:
            x[1].save()

        if not config.OpenWebif.auth.value:
            config.OpenWebif.auth_for_streaming.value = False
            config.OpenWebif.auth_for_streaming.save()

        if config.OpenWebif.enabled.value:
            HttpdRestart(global_session)
        else:
            HttpdStop(global_session)
        self.close()

    def keyCancel(self):
        for x in self["config"].list:
            x[1].cancel()
        self.close()


def confplug(session, **kwargs):
    session.open(OpenWebifConfig)


def IfUpIfDown(reason, **kwargs):
    LOG.info("IfUpIfDown({!r})".format(reason))

    try:
        if reason is True:
            HttpdStart(global_session)
        else:
            HttpdStop(global_session)
    except Exception as exc:
        LOG.error(exc)


def startSession(reason, session):
    LOG.info("startSession({!r})".format(session))
    global global_session
    global_session = session


def main_menu(menuid, **kwargs):
    LOG.info("main_menu({!r})".format(menuid))
    if menuid == "network":
        return [("OpenWebif", confplug, "openwebif", 45)]
    else:
        return []


def Plugins(**kwargs):
    result = [
        PluginDescriptor(
            where=[PluginDescriptor.WHERE_SESSIONSTART],
            fnc=startSession),
        PluginDescriptor(
            where=[PluginDescriptor.WHERE_NETWORKCONFIG_READ],
            fnc=IfUpIfDown),
    ]
    screenwidth = getDesktop(0).size().width()

    if imagedistro in ("openatv",):
        result.append(
            PluginDescriptor(
                name=PLUGIN_NAME,
                description=_("OpenWebif Configuration"),
                where=PluginDescriptor.WHERE_MENU,
                fnc=main_menu))

    if screenwidth and screenwidth == 1920:
        result.append(
            PluginDescriptor(
                name=PLUGIN_NAME,
                description=_("OpenWebif Configuration"),
                icon=PLUGIN_ICON_HD,
                where=[
                    PluginDescriptor.WHERE_PLUGINMENU],
                fnc=confplug))
    else:
        result.append(
            PluginDescriptor(
                name=PLUGIN_NAME,
                description=_("OpenWebif Configuration"),
                icon=PLUGIN_ICON,
                where=[
                    PluginDescriptor.WHERE_PLUGINMENU],
                fnc=confplug))

    return result

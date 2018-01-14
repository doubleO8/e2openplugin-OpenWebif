# -*- coding: utf-8 -*-
"""
..deprecated:: 0.27

    The entire module is crap.
"""
import os
import logging
import pprint
import xml.etree.cElementTree  # nosec

from enigma import eEnv
from Components.SystemInfo import SystemInfo
from Components.config import config

from ..i18n import _
from ..utilities import get_config_attribute

CONFIGFILES = None
LOG = logging.getLogger(__name__)


def addCollapsedMenu(name):
    tags = config.OpenWebif.webcache.collapsedmenus.value.split("|")
    if name not in tags:
        tags.append(name)

    config.OpenWebif.webcache.collapsedmenus.value = "|".join(tags).strip("|")
    config.OpenWebif.webcache.collapsedmenus.save()

    return {
        "result": True
    }


def removeCollapsedMenu(name):
    tags = config.OpenWebif.webcache.collapsedmenus.value.split("|")
    if name in tags:
        tags.remove(name)

    config.OpenWebif.webcache.collapsedmenus.value = "|".join(tags).strip("|")
    config.OpenWebif.webcache.collapsedmenus.save()

    return {
        "result": True
    }


def getCollapsedMenus():
    return {
        "result": True,
        "collapsed": config.OpenWebif.webcache.collapsedmenus.value.split("|")
    }


def setZapStream(value):
    config.OpenWebif.webcache.zapstream.value = value
    config.OpenWebif.webcache.zapstream.save()
    return {
        "result": True
    }


def getZapStream():
    return {
        "result": True,
        "zapstream": config.OpenWebif.webcache.zapstream.value
    }


def setShowChPicon(value):
    config.OpenWebif.webcache.showchannelpicon.value = value
    config.OpenWebif.webcache.showchannelpicon.save()
    return {
        "result": True
    }


def getShowChPicon():
    return {
        "result": True,
        "showchannelpicon": config.OpenWebif.webcache.showchannelpicon.value
    }


def getShowName():
    return {
        "result": True,
        "showname": config.OpenWebif.identifier.value
    }


def getCustomName():
    return {
        "result": True,
        "customname": config.OpenWebif.identifier_custom.value
    }


def getBoxName():
    return {
        "result": True,
        "boxname": config.OpenWebif.identifier_text.value
    }


def getJsonFromConfig(cnf):
    """

    ..deprecated:: 0.27

        This insanity shall be removed.

    """
    if cnf.__class__.__name__ == "ConfigSelection" or cnf.__class__.__name__ == "ConfigSelectionNumber" or cnf.__class__.__name__ == "TconfigSelection":
        if isinstance(cnf.choices.choices, dict):
            choices = []
            for choice in cnf.choices.choices:
                choices.append((choice, _(cnf.choices.choices[choice])))
        elif isinstance(cnf.choices.choices[0], tuple):
            choices = []
            for choice_tuple in cnf.choices.choices:
                choices.append((choice_tuple[0], _(choice_tuple[1])))
        else:
            choices = []
            for choice in cnf.choices.choices:
                choices.append((choice, _(choice)))

        return {
            "result": True,
            "type": "select",
            "choices": choices,
            "current": str(cnf.value)
        }
    elif cnf.__class__.__name__ == "ConfigBoolean" or cnf.__class__.__name__ == "ConfigEnableDisable" or cnf.__class__.__name__ == "ConfigYesNo":
        return {
            "result": True,
            "type": "checkbox",
            "current": cnf.value
        }
    elif cnf.__class__.__name__ == "ConfigSet":
        return {
            "result": True,
            "type": "multicheckbox",
            "choices": cnf.choices.choices,
            "current": cnf.value
        }

    elif cnf.__class__.__name__ == "ConfigNumber":
        return {
            "result": True,
            "type": "number",
            "current": cnf.value
        }
    elif cnf.__class__.__name__ == "ConfigInteger" or cnf.__class__.__name__ == "TconfigInteger":
        return {
            "result": True,
            "type": "number",
            "current": cnf.value,
            "limits": (cnf.limits[0][0], cnf.limits[0][1])
        }

    elif cnf.__class__.__name__ == "ConfigText":
        return {
            "result": True,
            "type": "text",
            "current": cnf.value
        }

    print "[OpenWebif] Unknown class ", cnf.__class__.__name__
    return {
        "result": False,
        "type": "unknown"
    }


def saveConfig(path, value):
    try:
        cnf = get_config_attribute(path, root_obj=config)
    except Exception as exc:
        print "[OpenWebif] ", exc
        return {
            "result": False,
            "message": "I'm sorry Dave, I'm afraid I can't do that"
        }

    try:
        if cnf.__class__.__name__ in (
                "ConfigBoolean",
                "ConfigEnableDisable",
                "ConfigYesNo"):
            cnf.value = value == "true"
        elif cnf.__class__.__name__ == "ConfigSet":
            values = cnf.value
            if int(value) in values:
                values.remove(int(value))
            else:
                values.append(int(value))
            cnf.value = values
        elif cnf.__class__.__name__ == "ConfigNumber":
            cnf.value = int(value)
        elif cnf.__class__.__name__ in ("ConfigInteger", "TconfigInteger"):
            cnf_min = int(cnf.limits[0][0])
            cnf_max = int(cnf.limits[0][1])
            cnf_value = int(value)
            if cnf_value < cnf_min:
                cnf_value = cnf_min
            elif cnf_value > cnf_max:
                cnf_value = cnf_max
            cnf.value = cnf_value
        else:
            cnf.value = value
        cnf.save()
    except Exception as e:
        print "[OpenWebif] ", e
        return {
            "result": False
        }

    return {
        "result": True
    }


def getConfigs(key):
    global CONFIGFILES

    configs = []
    title = None
    config_entries = None

    if not CONFIGFILES:
        CONFIGFILES = ConfigFiles()

    if not len(CONFIGFILES.sections):
        CONFIGFILES.getConfigs()

    if key in CONFIGFILES.section_config:
        config_entries = CONFIGFILES.section_config[key][1]
        title = CONFIGFILES.section_config[key][0]

    if config_entries:
        for entry in config_entries:
            try:
                LOG.info("entry.text={!r}".format(entry.text))
            except Exception as lexc:
                LOG.error(lexc)
            try:
                data = getJsonFromConfig(eval(entry.text or ""))  # nosec
                text = _(entry.get("text", ""))
                if "limits" in data:
                    text = "%s (%d - %d)" % (text,
                                             data["limits"][0],
                                             data["limits"][1])
                configs.append({
                    "description": text,
                    "path": entry.text or "",
                    "data": data
                })
            except Exception as e:
                LOG.error(e)

    return {
        "result": True,
        "configs": configs,
        "title": title
    }


def getConfigsSections():
    global CONFIGFILES

    if not CONFIGFILES:
        CONFIGFILES = ConfigFiles()

    if not len(CONFIGFILES.sections):
        CONFIGFILES.parseConfigFiles()
    return {
        "result": True,
        "sections": CONFIGFILES.sections
    }


def privSettingValues(prefix, top, result):
    for (key, val) in top.items():
        name = prefix + "." + key
        if isinstance(val, dict):
            privSettingValues(name, val, result)
        elif isinstance(val, tuple):
            result.append((name, val[0]))
        else:
            result.append((name, val))


def getSettings():
    configkeyval = []
    privSettingValues("config", config.saved_value, configkeyval)
    return {
        "result": True,
        "settings": configkeyval
    }


class ConfigFiles:
    def __init__(self):
        self.setupfiles = []
        self.sections = []
        self.section_config = {}
        self.allowedsections = [
            "usage",
            "userinterface",
            "recording",
            "subtitlesetup",
            "autolanguagesetup",
            "avsetup",
            "harddisk",
            "keyboard",
            "timezone",
            "time",
            "osdsetup",
            "epgsetup",
            "display",
            "remotesetup",
            "softcamsetup",
            "logs",
            "timeshift",
            "channelselection",
            "epgsettings",
            "softwareupdate",
            "pluginbrowsersetup"]
        self.log = logging.getLogger(__name__)
        self.getConfigFiles()

    def getConfigFiles(self):
        self.log.info("Getting")
        locations = ('SystemPlugins', 'Extensions')
        libdir = eEnv.resolve('${libdir}')
        datadir = eEnv.resolve('${datadir}')
        self.setupfiles = ['{:s}/enigma2/setup.xml'.format(datadir)]

        for location in locations:
            plugins = os.listdir('{:s}/enigma2/python/Plugins/{:s}'.format(
                libdir, location))

            for plugin in plugins:
                s_path = '{:s}/enigma2/python/Plugins/{:s}/{:s}/{:s}'.format(
                    libdir, location, plugin, "setup.xml")
                if os.path.isfile(s_path):
                    self.setupfiles.append(s_path)

        self.log.info(pprint.pformat({
            "setupfiles": self.setupfiles,
            "locations": locations,
            "libdir": libdir,
            "datadir": datadir,
        }))

    def parseConfigFiles(self):
        sections = []
        self.log.info("Parsing")

        for setupfile in self.setupfiles:
            # self.log.debug("Loading {!r}".format(setupfile))
            setupfile = file(setupfile, 'r')
            setupdom = xml.etree.cElementTree.parse(setupfile)  # nosec
            setupfile.close()
            xmldata = setupdom.getroot()

            for section in xmldata.findall("setup"):
                configs = []
                requires = section.get("requires")
                if requires and not SystemInfo.get(requires, False):
                    continue
                key = section.get("key")
                if key not in self.allowedsections:
                    showOpenWebIF = section.get("showOpenWebIF")
                    if showOpenWebIF == "1":
                        self.allowedsections.append(key)
                    else:
                        continue
                # self.log.debug("Loading section {!r}".format(key))

                for entry in section:
                    if entry.tag == "item":
                        requires = entry.get("requires")
                        if requires and not SystemInfo.get(requires, False):
                            continue

                        if int(entry.get("level",
                                         0)) > config.usage.setup_level.index:
                            continue
                        configs.append(entry)
                if len(configs):
                    sections.append({
                        "key": key,
                        "description": _(section.get("title"))
                    })
                    title = _(section.get("title", ""))
                    self.section_config[key] = (title, configs)
        sections = sorted(sections, key=lambda k: k['description'])
        self.sections = sections

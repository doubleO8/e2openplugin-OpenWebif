# -*- coding: utf-8 -*-

##############################################################################
#                        2011 E2OpenPlugins                                  #
#                                                                            #
#  This file is open source software; you can redistribute it and/or modify  #
#     it under the terms of the GNU General Public License version 2 as      #
#               published by the Free Software Foundation.                   #
#                                                                            #
##############################################################################
import os
import imp
import logging

from twisted.web import server, http, resource

from Plugins.Extensions.OpenWebif.__init__ import _
from Cheetah.Template import Template
from enigma import eEPGCache

from models.info import getInfo, getPublicPath, getViewsPath
from models.config import getCollapsedMenus, getConfigsSections
from models.config import getShowName, getCustomName, getBoxName


def new_getRequestHostname(self):
    host = self.getHeader(b'host')
    if host:
        if host[0] == '[':
            return host.split(']', 1)[0] + "]"
        return host.split(':', 1)[0].encode('ascii')
    return self.getHost().host.encode('ascii')


http.Request.getRequestHostname = new_getRequestHostname

REMOTE = ''

try:
    from boxbranding import getBoxType
except BaseException:
    from models.owibranding import getBoxType

try:
    from Components.RcModel import rc_model

    REMOTE = rc_model.getRcFolder() + "/remote"
except BaseException:
    from models.owibranding import rc_model

    REMOTE = rc_model().getRcFolder()

#: HTTP 404 Not Found response content
FOUR_O_FOUR = """
<html><head><title>Open Webif</title></head>
<body><h1>Error 404: Page not found</h1><br/>
The requested URL was not found on this server.</body></html>
"""


def error404(request):
    """
    HTTP 404 Not Found response.

    Args:
        request (twisted.web.server.Request): HTTP request object

    Returns:
        HTTP 404 Not Found response
    """
    request.setHeader("content-type", "text/html")
    request.setResponseCode(http.NOT_FOUND)
    request.write(FOUR_O_FOUR)
    request.finish()


class BaseController(resource.Resource):
    """
    Basic HTTP requests controller.
    """
    isLeaf = False

    def __init__(self, path="", **kwargs):
        """
        Constructor

        Args:
            path (basestring): Base path
            session: enigma2 Session instance
            withMainTemplate (bool): use main template
            isCustom (bool): custom output (?)
        """
        resource.Resource.__init__(self)

        self.path = path
        self.session = kwargs.get("session")
        self.withMainTemplate = kwargs.get("withMainTemplate", False)
        self.isCustom = kwargs.get("isCustom", False)
        self.log = logging.getLogger(__name__)
        self.themes_support = os.path.exists(getPublicPath('themes'))
        self._module_override = []

    def loadTemplate(self, template_trunk_relpath, module, args):
        self.log.debug("path={!r} module={!r} args={!r}".format(
            template_trunk_relpath, module, args))
        trunk = getViewsPath(template_trunk_relpath)
        template_file = None

        for ext in ('pyo', 'py', 'tmpl'):
            candy = '.'.join((trunk, ext))
            if os.path.isfile(candy):
                template_file = candy
                break

        if template_file is None:
            return None

        self.log.debug(">> {!r}".format(template_file))
        if template_file[-1] in ('o', 'y'):
            if template_file.endswith("o"):
                template = imp.load_compiled(module, template_file)
            else:
                template = imp.load_source(module, template_file)

            mod = getattr(template, module, None)
            if callable(mod):
                return str(mod(searchList=args))
        else:
            return str(Template(file=template_file, searchList=[args]))

        return None

    def getChild(self, path, request):
        return self.__class__(self.session, path)

    def render(self, request):
        # cache data
        withMainTemplate = self.withMainTemplate
        path = self.path
        isCustom = self.isCustom

        if self.path == "":
            self.path = "index"
        elif self.path == "signal":
            self.path = "tunersignal"
            request.uri = request.uri.replace('signal', 'tunersignal')
            request.path = request.path.replace('signal', 'tunersignal')

        self.path = self.path.replace(".", "")
        func = getattr(self, "P_" + self.path, None)
        if callable(func):
            request.setResponseCode(http.OK)

            # call prePageLoad function if exist
            plfunc = getattr(self, "prePageLoad", None)
            if callable(plfunc):
                plfunc(request)

            data = func(request)
            if data is None:
                error404(request)
            elif self.isCustom:
                request.write(data)
                request.finish()
            elif isinstance(data, str):
                request.setHeader("content-type", "text/plain")
                request.write(data)
                request.finish()
            else:
                try:
                    (tmpl_trunk,
                     template_module_name) = self._module_override.pop()
                except IndexError:
                    tmpl_trunk = request.path
                    template_module_name = self.path

                    if tmpl_trunk[-1] == "/":
                        tmpl_trunk += "index"
                    elif tmpl_trunk[-5:] != "index" and self.path == "index":
                        tmpl_trunk += "/index"

                    tmpl_trunk = tmpl_trunk.strip("/")
                    tmpl_trunk = tmpl_trunk.replace(".", "")

                # out => content
                out = self.loadTemplate(tmpl_trunk, template_module_name, data)
                if out is None:
                    self.log.error("Template not found for page {!r}".format(
                        request.uri))
                    error404(request)
                else:
                    if self.withMainTemplate:
                        args = self.prepareMainTemplate(request)
                        args["content"] = out
                        nout = self.loadTemplate("main", "main", args)
                        if nout:
                            out = nout
                    request.write(out)
                    request.finish()

        else:
            self.log.error("Page {!r} not found".format(request.uri))
            error404(request)

        # restore cached data
        self.withMainTemplate = withMainTemplate
        self.path = path
        self.isCustom = isCustom

        return server.NOT_DONE_YET

    def prepareMainTemplate(self, request):
        """
        Generate the `dict()` for main template.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            dict: Parameter values
        """
        ret = getCollapsedMenus()
        ginfo = getInfo()
        ret['configsections'] = getConfigsSections()['sections']
        ret['showname'] = getShowName()['showname']
        ret['customname'] = getCustomName()['customname']
        ret['boxname'] = getBoxName()['boxname']

        if not ret['boxname'] or not ret['customname']:
            ret['boxname'] = ginfo['brand'] + " " + ginfo['model']
        ret['box'] = getBoxType()
        ret["remote"] = REMOTE

        if hasattr(eEPGCache, 'FULL_DESCRIPTION_SEARCH'):
            ret['epgsearchcaps'] = True
        else:
            ret['epgsearchcaps'] = False

        ret['extras'] = [
            {'key': 'ajax/settings', 'description': _("Settings")}
        ]
        ret['theme'] = 'original-small-screen'

        return ret

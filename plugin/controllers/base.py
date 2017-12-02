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
from Cheetah.Template import Template

from models.info import getViewsPath

OWIF_PREFIX = 'P_'

#: HTTP 404 Not Found response content
FOUR_O_FOUR = """
<html><head><title>Open Webif</title></head>
<body><h1>Error 404: Page not found</h1><br/>
The requested URL was not found on this server.</body></html>
"""

TEMPLATE_E2_SIMPLE_XML_RESULT = "web/e2simplexmlresult"
TEMPLATE_E2_EVENT_LIST = "web/e2eventlist"
TEMPLATE_E2_SERVICE_LIST = "web/e2servicelist"
TEMPLATE_E2_TAGS = "web/e2tags"

TEMPLATE_ALIASES = {
    "web/epgservicenow": TEMPLATE_E2_EVENT_LIST,
    "web/timeraddbyeventid": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/mediaplayerplay": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/streamsubservices": TEMPLATE_E2_SERVICE_LIST,
    "web/timertogglestatus": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/subservices": TEMPLATE_E2_SERVICE_LIST,
    "web/timerlistwrite": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/recordnow": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/epgmulti": TEMPLATE_E2_EVENT_LIST,
    "web/epgservicenext": TEMPLATE_E2_EVENT_LIST,
    "web/message": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/pluginlistread": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/moviedelete": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/timeradd": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/removelocation": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/timerdelete": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/moviemove": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/mediaplayercmd": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/zap": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/movierename": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/parentcontrollist": TEMPLATE_E2_SERVICE_LIST,
    "web/saveepg": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/epgsearch": TEMPLATE_E2_EVENT_LIST,
    "web/mediaplayeradd": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/mediaplayerwrite": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/movietags": TEMPLATE_E2_TAGS,
    "web/messageanswer": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/servicelistreload": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/mediaplayerload": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/epgservice": TEMPLATE_E2_EVENT_LIST,
    "web/timerchange": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/timercleanup": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/mediaplayerremove": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/epgsimilar": TEMPLATE_E2_EVENT_LIST,
    "web/epgnext": TEMPLATE_E2_EVENT_LIST,
    "web/epgnownext": TEMPLATE_E2_EVENT_LIST,
    "web/epgnow": TEMPLATE_E2_EVENT_LIST
}


def new_getRequestHostname(self):
    host = self.getHeader(b'host')
    if host:
        if host[0] == '[':
            return host.split(']', 1)[0] + "]"
        return host.split(':', 1)[0].encode('ascii')
    return self.getHost().host.encode('ascii')


http.Request.getRequestHostname = new_getRequestHostname


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
            isCustom (bool): custom output (?)
        """
        resource.Resource.__init__(self)

        self.path = path
        self.session = kwargs.get("session")
        self.isCustom = kwargs.get("isCustom", False)
        self.log = logging.getLogger(__name__)
        self._module_override = []
        self.verbose = 11

    def _push_module_template(self, trunk, module_name=None, prefix=None):
        if module_name is None:
            module_name = trunk
        if prefix is not None:
            trunk = '/'.join((trunk, prefix))

        self._module_override.append((trunk, module_name))

    def loadTemplate(self, template_trunk_relpath, module, args):
        if self.verbose > 10:
            self.log.debug(
                "template_trunk_relpath={!r} module={!r} args={!r}".format(
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

        # self.log.debug(">> {!r}".format(template_file))
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
        path = self.path
        isCustom = self.isCustom

        if self.path == "":
            self.path = "index"
        elif self.path == "signal":
            self.path = "tunersignal"
            request.uri = request.uri.replace('signal', 'tunersignal')
            request.path = request.path.replace('signal', 'tunersignal')
        self.path = self.path.replace(".", "")

        owif_func = OWIF_PREFIX + self.path
        self.log.warning(owif_func)
        func = getattr(self, owif_func, None)
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

                if tmpl_trunk in TEMPLATE_ALIASES:
                    the_alias =TEMPLATE_ALIASES[tmpl_trunk]
                    template_module_name = os.path.basename(the_alias)
                    self.log.warning("Template alias {!r} -> {!r}".format(
                        tmpl_trunk, the_alias))
                    tmpl_trunk = the_alias

                # out => content
                out = self.loadTemplate(tmpl_trunk, template_module_name, data)
                if out is None:
                    self.log.error("Template not found for page {!r}".format(
                        request.uri))
                    error404(request)
                else:
                    request.write(out)
                    request.finish()
        else:
            self.log.error("Page {!r} not found".format(request.uri))
            error404(request)

        # restore cached data
        self.path = path
        self.isCustom = isCustom

        return server.NOT_DONE_YET

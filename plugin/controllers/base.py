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

from defaults import VIEWS_PATH
from utilities import mangle_host_header_port

OWIF_PREFIX = 'P_'

#: HTTP 404 Not Found response content
FOUR_O_FOUR = """
<html><head><title>Open Webif</title></head>
<body><h1>Error 404: Page not found</h1><br/>
The requested URL was not found on this server.</body></html>
"""

#: template for simple XML result
TEMPLATE_E2_SIMPLE_XML_RESULT = "web/e2simplexmlresult"

#: template for enigma2 event list
TEMPLATE_E2_EVENT_LIST = "web/e2eventlist"

#: template for enigma2 service list
TEMPLATE_E2_SERVICE_LIST = "web/e2servicelist"

#: template for enigma2 tags
TEMPLATE_E2_TAGS = "web/e2tags"

#: template aliases
TEMPLATE_ALIASES = {
    "web/loadepg": TEMPLATE_E2_SIMPLE_XML_RESULT,
    "web/epgbouquet": TEMPLATE_E2_EVENT_LIST,
    "web/getservices": TEMPLATE_E2_SERVICE_LIST,
    "web/gettags": TEMPLATE_E2_TAGS,
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
    "web/epgnow": TEMPLATE_E2_EVENT_LIST,
}

CONTENT_TYPE_X_MPEGURL = 'application/x-mpegurl'
CONTENT_TYPE_HTML = 'text/html'
CONTENT_TYPE_TEXT = 'text/plain'
CONTENT_TYPE_JSON = 'application/json; charset=utf-8'


def error404(request):
    """
    HTTP 404 Not Found response.

    Args:
        request (twisted.web.server.Request): HTTP request object

    Returns:
        HTTP 404 Not Found response
    """
    request.setHeader("content-type", CONTENT_TYPE_HTML)
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
        """
        resource.Resource.__init__(self)
        self.path = path
        self.session = kwargs.get("session")
        self.log = logging.getLogger(__name__)
        self.content_type = None
        self.verbose = 0

    def loadTemplate(self, template_trunk_relpath, module, args):
        """
        Try to generate template contents by trying to load optimised bytecode,
        python sourcefile and `.tmpl` file (in that order).

        Args:
            template_trunk_relpath (basestring): template filename trunk
            module (basestring): module name
            args (dict): template parameters

        Returns:
            str: template content

        """
        if self.verbose > 10:
            self.log.debug(
                "template_trunk_relpath={!r} module={!r} args={!r}".format(
                    template_trunk_relpath, module, args))

        trunk = '/'.join((VIEWS_PATH, template_trunk_relpath))
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
        if self.verbose:
            fmt = "{scheme}://{netloc}{path} " \
                  "accessed by {client}{via} {r_args}"
            args = mangle_host_header_port(request.getHeader('host'))
            args['path'] = request.path
            try:
                args['client'] = request.transport.getPeer()
            except Exception as exc:
                self.log.error(exc)
                args['client'] = request.getClient()
            args['via'] = ''

            header = request.getHeader("X-Forwarded-For")
            if header:
                args['via'] = " ({!r})".format(header.split(",")[-1].strip())

            args['r_args'] = request.args
            self.log.info(fmt.format(**args))
            if self.verbose > 4:
                self.log.debug(request.getAllHeaders())

        # cache data
        path = self.path

        if self.path == "":
            self.path = "index"

        self.path = self.path.replace(".", "")
        owif_callback_name = OWIF_PREFIX + self.path
        func = getattr(self, owif_callback_name, None)

        if self.verbose > 10:
            self.log.info('{!r} {!r}'.format(owif_callback_name, func))

        if callable(func):
            data = func(request)
            if data is None:
                self.log.warning('{!r} {!r} returned None'.format(
                    owif_callback_name, func))
                error404(request)
                return server.NOT_DONE_YET

            if self.content_type:
                request.setHeader("content-type", self.content_type)

            if self.content_type == CONTENT_TYPE_X_MPEGURL:
                request.write(data)
                request.finish()
            elif isinstance(data, str):
                request.setHeader("content-type", CONTENT_TYPE_TEXT)
                request.write(data)
                request.finish()
            else:
                tmpl_trunk = request.path
                template_module_name = self.path

                if tmpl_trunk[-1] == "/":
                    tmpl_trunk += "index"
                elif tmpl_trunk[-5:] != "index" and self.path == "index":
                    tmpl_trunk += "/index"

                tmpl_trunk = tmpl_trunk.strip("/")
                tmpl_trunk = tmpl_trunk.replace(".", "")

                if tmpl_trunk in TEMPLATE_ALIASES:
                    the_alias = TEMPLATE_ALIASES[tmpl_trunk]
                    template_module_name = os.path.basename(the_alias)
                    if self.verbose > 10:
                        self.log.warning("Template alias {!r} -> {!r}".format(
                            tmpl_trunk, the_alias))
                    tmpl_trunk = the_alias

                # out => content
                out = self.loadTemplate(tmpl_trunk, template_module_name, data)
                if out is None:
                    self.log.error(
                        "Template not loadable for {!r} (page {!r})".format(
                            owif_callback_name, request.uri))
                    error404(request)
                else:
                    request.write(out)
                    request.finish()
        else:
            self.log.error("Callback {!r} for page {!r} not found".format(
                owif_callback_name, request.uri))
            error404(request)

        # restore cached data
        self.path = path

        return server.NOT_DONE_YET

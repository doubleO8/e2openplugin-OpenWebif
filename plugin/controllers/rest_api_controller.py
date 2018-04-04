#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RESTful API access using HTTP
-----------------------------

This controller exposes the application programming interface (API) as
implemented by the :py:class:`controllers.web` and :py:class:`controllers.ajax`
controllers.

The generated responses are returned as JSON data with appropriate HTTP
headers. Output will be compressed using gzip if requested by client.

A swagger v2 (https://swagger.io/) compatible API specification will be
returned when accessing the /api/ endpoint. The API specification is consumable
e.g. by a Swagger UI (https://swagger.io/swagger-ui/) instance.
"""
import urlparse
import copy
import os
import json

from twisted.web import http, resource
from twisted.web.resource import EncodingResourceWrapper
from twisted.web.server import GzipEncoderFactory

from rest import json_response, CORS_ALLOWED_METHODS_DEFAULT, CORS_DEFAULT
from rest import CORS_DEFAULT_ALLOW_ORIGIN
from utilities import mangle_host_header_port, gen_reverse_proxy_configuration

HAVE_E2_CONTROLLER = True
TOW_FRONTEND = False

try:
    from web import WebController
except ImportError:
    HAVE_E2_CONTROLLER = False

if HAVE_E2_CONTROLLER:
    try:
        from ajax import AjaxController
        TOW_FRONTEND = True
    except ImportError:
        pass

    from rest_saveconfig_api import SaveConfigApiController
    from rest_eventlookup_api import EventLookupApiController
    from rest_eventsearch_api import EventSearchApiController
    from evil_proxy import EvilProxyController

#: OpenAPI specification source (swagger.json)
SWAGGER_TEMPLATE = os.path.join(
    os.path.dirname(__file__), 'swagger.json')

#: prefix for OpenWebif controller methods
OWIF_PREFIX = 'P_'


class ApiController(resource.Resource):
    isLeaf = False

    def __init__(self, session, path="", *args, **kwargs):
        resource.Resource.__init__(self)
        self.web_instance = None
        self.ajax_instance = None

        if HAVE_E2_CONTROLLER:
            self.putChild("saveconfig",
                          SaveConfigApiController(session=session, path=path))
            self.putChild("eventlookup", EventLookupApiController())
            self.putChild("eventsearch", EventSearchApiController())
            self.putChild("evil", EvilProxyController(session=session))

            #: web controller instance
            self.web_instance = WebController(session, path)
            if TOW_FRONTEND:
                #: ajax controller instance
                self.ajax_instance = AjaxController(session, path)

        self.verbose = kwargs.get("verbose", 1)
        self._resource_prefix = kwargs.get("resource_prefix", '/api')
        self._cors_header = copy.copy(CORS_DEFAULT)
        http_verbs = []

        for verb in CORS_ALLOWED_METHODS_DEFAULT:
            method_name = 'render_{:s}'.format(verb)
            if hasattr(self, method_name):
                http_verbs.append(verb)
        self._cors_header['Access-Control-Allow-Methods'] = ','.join(
            http_verbs)

    def getChild(self, path, request):
        if path in self.children:
            return self.children[path]
        return EncodingResourceWrapper(self, [GzipEncoderFactory()])

    def render_OPTIONS(self, request):
        """
        Render response for an HTTP OPTIONS request.

        Args:
            request (:obj:`twisted.web.server.Request`): HTTP request object
        Returns:
            HTTP response with headers
        """
        for key in self._cors_header:
            request.setHeader(key, self._cors_header[key])

        return ''

    def _index(self, request):
        """
        Return a swagger/JSON based description of the implemented interface.

        Args:
                request (twisted.web.server.Request): HTTP request object
        Returns:
                HTTP response with headers
        """
        with open(SWAGGER_TEMPLATE, "rb") as src:
            data = json.load(src)

        return json_response(request, data)

    def _reverse_proxy_configuration(self, request):
        """
        Return an example configuration for nginx acting as a reverse proxy
        for the current device.

        Args:
                request (twisted.web.server.Request): HTTP request object
        Returns:
                HTTP response with headers
        """
        mangled = mangle_host_header_port(request.getHeader('host'))
        configuration = {
            "ENIGMA2_HOST": mangled['hostname'],
            "ENIGMA2_PORT": 80,
            "OSCAM_PORT": 83,
            "STREAM_PORT": 8001,
            "STREAM_TRANSCODED_PORT": 8002,
            "PUBLIC_ROOT": '/tmp/public',
            "PICON_ROOT": '/tmp/picon',
        }

        request.setHeader("content-type", "text/plain")
        return gen_reverse_proxy_configuration(configuration)

    def render_GET(self, request):
        """
        HTTP GET implementation.

        Args:
                request (twisted.web.server.Request): HTTP request object
        Returns:
                HTTP response with headers
        """
        rq_path = urlparse.unquote(request.path)

        if not rq_path.startswith(self._resource_prefix):
            raise ValueError("Invalid Request Path {!r}".format(request.path))

        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        # as implemented in BaseController -----------------v
        func_path = rq_path[len(self._resource_prefix) + 1:].replace(".", "")

        if func_path in ("", "index"):
            return self._index(request)

        if func_path == 'reverse_proxy_conf':
            return self._reverse_proxy_configuration()

        #: name of OpenWebif method to be called
        owif_func = "{:s}{:s}".format(OWIF_PREFIX, func_path)

        #: callable methods
        funcs = [
            # TODO: add method of *self*
            ('web', getattr(self.web_instance, owif_func, None)),
        ]

        if self.ajax_instance is not None:
            funcs.append(
                ('ajax', getattr(self.ajax_instance, owif_func, None)))

        #: method to be called
        func = None
        #: nickname for controller instance
        source_controller = None

        # query controller instances for given method - first match wins
        for candidate_controller, candidate in funcs:
            if callable(candidate):
                func = candidate
                source_controller = candidate_controller
                break

        if func is None:
            request.setResponseCode(http.NOT_FOUND)
            data = {
                "method": repr(func_path),
                "result": False,
            }

            if self.verbose:
                data["request"] = {
                    "path": request.path,
                    "postpath": request.postpath,
                    "mangled_host_header": mangle_host_header_port(
                        request.getHeader('host')),
                    "host_header": request.getHeader('host')
                }

            return json_response(request, data)

        try:
            request.setResponseCode(http.OK)
            data = func(request)
            data['_controller'] = source_controller
            try:
                if "result" not in data:
                    data["result"] = True
            except Exception:
                # ignoring exceptions is bad.
                pass

            return json_response(data=data, request=request)
        except Exception as exc:
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)
            data = {
                "exception": repr(exc),
                "result": False,
                "path": request.path,
            }

            return json_response(request, data)


if __name__ == '__main__':
    from twisted.web.server import Site
    from twisted.internet import reactor

    root = ApiController(session=None)
    root.putChild("api", ApiController(session=False))
    factory_r = Site(root)

    reactor.listenTCP(19999, factory_r)
    reactor.run()

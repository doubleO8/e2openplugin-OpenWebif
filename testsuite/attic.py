#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import re

from twisted.web.server import Site, resource
from twisted.internet import reactor

# hack: alter include path in such ways that utilities library is included
sys.path.append(os.path.join(os.path.dirname(__file__),
                             '../plugin/controllers'))

from rest import RESTControllerSkeleton
from rest import json_response, CORS_DEFAULT_ALLOW_ORIGIN
from utilities import mangle_host_header_port


def new_getRequestHostname(request):
    host = request.getHeader(b'host')
    if host:
        if host[0] == '[':
            return host.split(']', 1)[0] + "]"
        return host.split(':', 1)[0].encode('ascii')
    return request.getHost().host.encode('ascii')


def whoami(request, fallback_port=None):
    #: port fallback is ``comp_config.OpenWebif.port.value`` actually
    if fallback_port is None:
        port = "8088"
    else:
        port = fallback_port
    proto = 'http'
    ourhost = request.getHeader('host')
    m = re.match('.+\:(\d+)$', ourhost)
    if m is not None:
        port = m.group(1)
    return {'proto': proto, 'port': port}


class WhoamiControl(RESTControllerSkeleton):
    def render_GET(self, request):
        """
        HTTP GET implementation.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        data = {
            "_controller": self.__class__.__name__,
            "request_postpath": request.postpath,
            "method": request.method,
            "request_path": request.path,
            "request_header_host": request.getHeader("host"),
            "request_hostname": request.getRequestHostname(),
            "same_same": False,
        }
        fallback_port = "8010"
        try:
            data['whoami_result'] = whoami(request,
                                           fallback_port=fallback_port)
        except Exception as exc:
            data['whoami_result'] = 'FAIL: {!r}'.format(exc)

        try:
            data['mangle_host_header_port'] = mangle_host_header_port(
                request.getHeader("host"), fallback_port=fallback_port)
        except Exception as exc:
            data['mangle_host_header_port'] = 'FAIL: {!r}'.format(exc)

        data['monkey_host'] = new_getRequestHostname(request)

        try:
            a = data['whoami_result']
            b = data['mangle_host_header_port']
            keys = ('port', 'proto')
            data['same_same'] = True
            for key in keys:
                if a[key] != b[key]:
                    data['same_same'] = False
                    break
        except Exception:
            pass
        return json_response(request, data)


class AnotherSimpleRootController(resource.Resource):
    """
    Simple (Web) Root Controller.
    """
    isLeaf = False

    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild("demo", WhoamiControl())
        self.putChild("", WhoamiControl())


if __name__ == '__main__':
    root = AnotherSimpleRootController()
    factory_r = Site(root)

    reactor.listenTCP(19999, factory_r)
    reactor.run()

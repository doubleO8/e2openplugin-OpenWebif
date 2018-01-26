#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import copy
import logging

from twisted.web import resource, http

from utilities import get_servicereference_portions, add_expires_header

#: CORS - HTTP headers the client may use
CORS_ALLOWED_CLIENT_HEADERS = [
    'Content-Type',
]

#: CORS - HTTP methods the client may use
CORS_ALLOWED_METHODS_DEFAULT = ['GET', 'PUT', 'POST', 'DELETE', 'OPTIONS']

#: CORS - default origin header value
CORS_DEFAULT_ALLOW_ORIGIN = '*'

#: CORS - HTTP headers the server will send as part of OPTIONS response
CORS_DEFAULT = {
    'Access-Control-Allow-Origin': CORS_DEFAULT_ALLOW_ORIGIN,
    'Access-Control-Allow-Credentials': 'true',
    'Access-Control-Max-Age': '86400',
    'Access-Control-Allow-Methods': ','.join(CORS_ALLOWED_METHODS_DEFAULT),
    'Access-Control-Allow-Headers': ', '.join(CORS_ALLOWED_CLIENT_HEADERS)
}


def json_response(request, data, indent=1):
    """
    Create a JSON representation for *data* and set HTTP headers indicating
    that JSON encoded data is returned.

    Args:
        request (twisted.web.server.Request): HTTP request object
        data: response content
        indent: indentation level or None
    Returns:
        JSON representation of *data* with appropriate HTTP headers
    """
    request.setHeader("content-type", "application/json; charset=utf-8")
    return json.dumps(data, indent=indent)


class RESTControllerSkeleton(resource.Resource):
    """
    Skeleton implementation of a RESTful contoller class.
    """
    isLeaf = True

    def __init__(self, *args, **kwargs):
        resource.Resource.__init__(self)
        self._cors_header = copy.copy(CORS_DEFAULT)
        http_verbs = []
        self.session = kwargs.get("session")

        for verb in CORS_ALLOWED_METHODS_DEFAULT:
            method_name = 'render_{:s}'.format(verb)
            if hasattr(self, method_name):
                http_verbs.append(verb)
        self._cors_header['Access-Control-Allow-Methods'] = ','.join(
            http_verbs)

    def _cache(self, request, expires=False):
        add_expires_header(request, expires=expires)

    def render_OPTIONS(self, request):
        """
        Render response for an HTTP OPTIONS request.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        for key in self._cors_header:
            request.setHeader(key, self._cors_header[key])

        return ''

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
        }

        return json_response(request, data)

    def render_POST(self, request):
        """
        HTTP POST implementation.

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
        }

        return json_response(request, data)

    def error_response(self, request, response_code=None, **kwargs):
        """
        Create and return an HTTP error response with data as JSON.

        Args:
                request (twisted.web.server.Request): HTTP request object
                response_code: HTTP Status Code (default is 500)
                **kwargs: additional key/value pairs
        Returns:
                JSON encoded data with appropriate HTTP headers
        """
        if response_code is None:
            response_code = http.INTERNAL_SERVER_ERROR

        response_data = {
            "_request": {
                "path": request.path,
                "postpath": request.postpath,
                "uri": request.uri,
                "method": request.method,
            },
            "result": False,
        }

        response_data.update(**kwargs)

        request.setResponseCode(response_code)
        return json_response(request, response_data)


class TwoFaceApiController(RESTControllerSkeleton):
    def __init__(self, *args, **kwargs):
        RESTControllerSkeleton.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)

    def render_list_all(self, request):
        data = dict(result=True, items=[])

        # override

        return json_response(request, data)

    def render_list_subset(self, request, service_reference):
        data = dict(result=True, items=[],
                    service_reference=service_reference)

        # override

        return json_response(request, data)

    def render_list_item(self, request, service_reference, item_id):
        data = dict(result=True, items=[],
                    service_reference=service_reference,
                    item_id=item_id)

        # override

        if not data['items']:
            request.setResponseCode(http.NOT_FOUND)

        return json_response(request, data)

    def _mangle_args(self, request, needed=2):
        item_id = None
        pp_len = len(request.postpath)

        if pp_len < needed:
            raise ValueError(
                "Bad postpath length: Needed {:d}, GOIT {:d}".format(
                    needed, pp_len))

        for index in range(needed):
            if not request.postpath[index]:
                raise ValueError("Empty postpath[{:d}], {!r}".format(
                    index, request.postpath))

        portions = get_servicereference_portions(request.postpath[0])
        if len(portions) == 0:
            raise ValueError("Bad portions length: {:d}".format(
                len(portions)))

        service_reference = ':'.join(portions)

        if pp_len > 1:
            try:
                item_id = int(request.postpath[1])
            except Exception:
                if needed > 1:
                    raise

        return service_reference, item_id

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
        pp_len = len(request.postpath)

        if pp_len == 0 or (pp_len == 1 and not request.postpath[0]):
            return self.render_list_all(request)

        try:
            service_reference, item_id = self._mangle_args(request, needed=1)
        except ValueError as vexc:
            item_id = None
            service_reference = None
            request.setResponseCode(http.BAD_REQUEST)
            self.log.error(vexc.message)

        if service_reference and item_id:
            return self.render_list_item(request, service_reference, item_id)
        elif service_reference:
            return self.render_list_subset(request, service_reference)

        data = {
            "result": False,
            "_controller": self.__class__.__name__,
            "request": {
                "postpath": request.postpath,
                "path": request.path,
                "args": request.args,
            }
        }

        return json_response(request, data)


class SimpleRootController(resource.Resource):
    """
    Simple (Web) Root Controller.
    """
    isLeaf = False

    def __init__(self):
        resource.Resource.__init__(self)
        self.putChild("demo", RESTControllerSkeleton())
        self.putChild("", RESTControllerSkeleton())


if __name__ == '__main__':
    from twisted.web.server import Site
    from twisted.internet import reactor

    root = SimpleRootController()
    # root.putChild("configuration", RESTControllerSkeleton())
    factory_r = Site(root)

    reactor.listenTCP(19999, factory_r)
    reactor.run()

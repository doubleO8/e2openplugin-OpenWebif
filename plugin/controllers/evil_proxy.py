#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import StringIO
import contextlib

from twisted.web import http

from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton


@contextlib.contextmanager
def stdout_ctx(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = StringIO.StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old


class EvilProxyController(RESTControllerSkeleton):
    """
    A rather evil controller - allows arbitrary execution of python code.

    .. warning::

        DANGER, WILL ROBINSON! Never ever allow unrestricted access to this
        endpoint!
    """

    def __init__(self, *args, **kwargs):
        RESTControllerSkeleton.__init__(self, *args, **kwargs)
        self.ession = kwargs.get("session")

    def render_POST(self, request):
        """
        Execute python code defined by request parameter *uma*.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers

        .. http:post:: /api/evil

            :query string uma: python code snippet to be executed

        """
        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        uma = request.args['uma'][0]
        data = {
            "_controller": self.__class__.__name__,
            "uma": False
        }

        with stdout_ctx() as s:
            try:
                exec (uma)
                data['uma'] = True
            except Exception as exc:
                data['exception'] = repr(exc)
                request.setResponseCode(http.INTERNAL_SERVER_ERROR)
        data['stdout'] = s.getvalue()

        return json_response(request, data)

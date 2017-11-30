#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RESTful Controller for /api/eventlookup endpoint
================================================

"""
from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton
from events import EventsController


class EventLookupApiController(RESTControllerSkeleton):
    def __init__(self, *args, **kwargs):
        RESTControllerSkeleton.__init__(self, *args, **kwargs)
        self.ec_instance = EventsController()

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

        mangled_parameters = dict(
            flags=None,
            service_reference=None  # '1:0:19:7C:6:85:FFFF0000:0:0:0:'
        )

        for key in ("flags", "service_reference"):
            if key in request.args:
                mangled_parameters[key] = request.args[key][0]

        for key in ("querytype", "max_rows", "begin", "minutes"):
            try:
                value = int(request.args[key][0])
            except (KeyError, TypeError, ValueError):
                value = None
            mangled_parameters[key] = value

        data = {
            "errors": [],
            "result": False,
            "mangled_parameters": mangled_parameters,
            "len": 0
        }

        if mangled_parameters["service_reference"]:
            try:
                data['events'] = self.ec_instance.lookup(**mangled_parameters)
                data['result'] = True
                data['len'] = len(data['events'])
            except Exception as exc:
                data['errors'].append(repr(exc))

        return json_response(request, data)

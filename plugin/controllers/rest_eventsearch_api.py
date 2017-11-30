#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RESTful Controller for /api/eventsearch endpoint
================================================

"""
from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton

from events import EventsController


class EventSearchApiController(RESTControllerSkeleton):
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
            case_sensitive=False,
            flags=None,
            what=None

        )

        if "flags" in request.args:
            mangled_parameters["flags"] = request.args["flags"][0]

        for key in ("querytype", "max_rows"):
            try:
                value = int(request.args[key][0])
            except:
                value = None
            mangled_parameters[key] = value

        if request.args.get("case_sensitive", [False])[0]:
            mangled_parameters["case_sensitive"] = True

        data = {
            "errors": [],
            "result": False,
            "mangled_parameters": mangled_parameters,
            "len": 0
        }

        try:
            what = request.args["what"][0]
        except KeyError:
            data['errors'].append("Nothing to search for?!")
        except Exception as exc1:
            data['errors'].append(repr(exc1))


        if mangled_parameters["what"]:
            try:
                data['events'] = self.ec_instance.search(
                    what=mangled_parameters["what"],
                    querytype=mangled_parameters.get("querytype"),
                    max_rows=mangled_parameters.get("max_rows"),
                    case_sensitive=mangled_parameters.get("case_sensitive"),
                    flags=mangled_parameters.get("flags"))
                data['result'] = True
                data['len'] = len(data['events'])
            except Exception as exc:
                data['errors'].append(repr(exc))

        return json_response(request, data)

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

        if "flags" in request.args:
            flags = request.args["flags"][0]
        else:
            flags = None

        mangled_parameters = dict()

        for key in ("querytype", "max_rows"):
            try:
                value = int(request.args[key][0])
            except:
                value = None
            mangled_parameters[key] = value

        case_sensitive = False
        if request.args.get("case_sensitive", [False])[0]:
            case_sensitive = True

        data = {
            "errors": [],
            "result": False,
        }

        try:
            what = request.args["what"][0]
        except KeyError:
            data['errors'].append("Nothing to search for?!")
        except Exception as exc1:
            data['errors'].append(repr(exc1))
            what = None

        data = {
            "result": False,
            "args": {
                "lookup_flags": flags,
                "mangled_parameters": mangled_parameters,
            }
        }

        if what:
            try:
                data['events'] = self.ec_instance.search(
                    what,
                    querytype=mangled_parameters.get("querytype"),
                    max_rows=mangled_parameters.get("max_rows"),
                    case_sensitive=case_sensitive,
                    flags=flags)
                data['result'] = True
                data['len'] = len(data['events'])
            except Exception as exc:
                data['exception'] = repr(exc)

        return json_response(request, data)

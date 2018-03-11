#!/usr/bin/env python
# -*- coding: utf-8 -*-
from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton
from events import EventsController


class EventSearchApiController(RESTControllerSkeleton):
    """
    RESTful Controller for ``/api/eventsearch`` endpoint
    """
    def __init__(self, *args, **kwargs):
        RESTControllerSkeleton.__init__(self, *args, **kwargs)
        self.ec_instance = EventsController()

    def render_GET(self, request):
        """
        HTTP GET implementation.

        .. seealso::

            * *querytype* Parameter – :ref:`event_search_parameters-label`
            * *flags* Parameter – :ref:`event_format-label`

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers

        .. http:get:: /api/eventsearch

            :query basestring what: search term
            :query int querytype: (optional) query type
            :query basestring flags: (optional) fields to be returned
            :query int max_rows: (optional) maximum number of result rows

            :statuscode 200: no error
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
            except Exception:
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
            mangled_parameters["what"] = request.args["what"][0]
        except KeyError:
            data['errors'].append("Nothing to search for?!")
        except Exception as exc1:
            data['errors'].append(repr(exc1))

        if mangled_parameters["what"]:
            try:
                data['events'] = self.ec_instance.search(**mangled_parameters)
                data['result'] = True
                data['len'] = len(data['events'])
            except Exception as exc:
                data['errors'].append(repr(exc))

        return json_response(request, data)

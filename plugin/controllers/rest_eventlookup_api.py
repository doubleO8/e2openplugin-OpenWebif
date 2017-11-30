#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RESTful Controller for /api/eventlookup endpoint
================================================


"""
from enigma import eEPGCache
from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton

QUERYTYPE_LOOKUP__BEFORE = -1
QUERYTYPE_LOOKUP__WHILE = 0
QUERYTYPE_LOOKUP__AFTER = 1
QUERYTYPE_LOOKUP__ID = 2

QUERY_TIMESTAMP_CURRENT_TIME = -1
QUERY_MINUTES_ANY = -1


class EventLookupApiController(RESTControllerSkeleton):
    def __init__(self, *args, **kwargs):
        RESTControllerSkeleton.__init__(self, *args, **kwargs)
        self.epgcache_instance = eEPGCache.getInstance()

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
            flags = 'IBDTSERN'

        if "sref" in request.args:
            service_reference = request.args["sref"][0]
        else:
            service_reference = '1:0:19:7C:6:85:FFFF0000:0:0:0:'

        arg_0 = {
            "querytype": QUERYTYPE_LOOKUP__WHILE,
            "begin": QUERY_TIMESTAMP_CURRENT_TIME,
            "minutes": QUERY_MINUTES_ANY,
        }

        for key in set(arg_0.keys()):
            try:
                value = int(request.args[key][0])
                arg_0[key] = value
            except:
                pass

        arglist = (service_reference,
                   arg_0['querytype'], arg_0['begin'], arg_0['minutes'])

        data = {
            "result": False,
            "args": {
                "lookup_flags": flags,
                "service_reference": service_reference,
                "arg_0": arg_0,
            }
        }

        try:
            data['events'] = self.epgcache_instance.lookupEvent(
                [flags, arglist]
            )
            data['result'] = True
            data['len'] = len(data['events'])
        except Exception as exc:
            data['exception'] = repr(exc)

        return json_response(request, data)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RESTful Controller for /api/eventlookup endpoint
"""
from enigma import eEPGCache
from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton


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
            service_reference = 'IBDTSERN'

        data = {
            "result": False,
            "args": {
                "flags": flags,
                "service_reference": service_reference
            }
        }
        try:
            data['events'] = self.epgcache_instance.lookupEvent(
                [flags, (service_reference, 0, 0, -1), (service_reference, 0, 1, -1)]
            )
        except Exception as exc:
            data['exception'] = repr(exc)

        return json_response(request, data)

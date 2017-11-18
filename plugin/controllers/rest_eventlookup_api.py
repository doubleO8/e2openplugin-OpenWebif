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
            service_reference = '1:0:19:7C:6:85:FFFF0000:0:0:0:'

        data = {
            "result": False,
            "_search_flags": [
                ("SIMILAR_BROADCASTINGS_SEARCH", self.epgcache_instance.SIMILAR_BROADCASTINGS_SEARCH),
                ("EXAKT_TITLE_SEARCH", self.epgcache_instance.EXAKT_TITLE_SEARCH),
                ("PARTIAL_TITLE_SEARCH", self.epgcache_instance.PARTIAL_TITLE_SEARCH),
                ("SHORT_DESCRIPTION_SEARCH", self.epgcache_instance.SHORT_DESCRIPTION_SEARCH),
                ("TITLE_SHORT_DESCRIPTION_SEARCH", self.epgcache_instance.TITLE_SHORT_DESCRIPTION_SEARCH),
                ("EXTENDED_DESCRIPTION_SEARCH", self.epgcache_instance.EXTENDED_DESCRIPTION_SEARCH),
                ("FULL_DESCRIPTION_SEARCH", self.epgcache_instance.FULL_DESCRIPTION_SEARCH),
                ("CASE_CHECK", self.epgcache_instance.CASE_CHECK),
                ("NO_CASE_CHECK", self.epgcache_instance.NO_CASE_CHECK),
            ],
            "args": {
                "lookup_flags": flags,
                "service_reference": service_reference
            }
        }

        #                    service_type
        # service_reference, ?,
        #                    0, begintime, endtime
        #                    2, ID # lookup by ID?
        #                    0, -1        # NOW
        #                    1, -1        # NEXT
        #                    0, -1, -1    # Service
        try:
            data['events'] = self.epgcache_instance.lookupEvent(
                [flags, (service_reference, 0, 0, -1), (service_reference, 0, 1, -1)]
            )
            data['result'] = True
        except Exception as exc:
            data['exception'] = repr(exc)

        return json_response(request, data)

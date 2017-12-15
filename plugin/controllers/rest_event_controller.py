#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Event Items
-----------

Listing of event items on current device.
"""
import logging

from twisted.web import http

from rest import json_response
from rest import TwoFaceApiController
from events import EventsController
from events import QUERYTYPE_LOOKUP__WHILE, QUERY_TIMESTAMP_CURRENT_TIME


class RESTEventController(TwoFaceApiController):
    """
    RESTful Controller for /events endpoint.

    .. http:get:: /events/{basestring:service_reference}/

        :statuscode 200: no error
        :statuscode 400: invalid

    """

    def __init__(self, *args, **kwargs):
        TwoFaceApiController.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)
        self.session = kwargs.get("session")
        self.ec = EventsController()

    def render_list_all(self, request):
        """
        Not supported

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        try:
            service_reference = self.session.nav.getCurrentlyPlayingServiceReference().toString()
            return self.render_list_subset(request, service_reference)
        except Exception:
            return self.error_response(request, response_code=http.NOT_FOUND)

    def render_list_subset(self, request, service_reference):
        """
        List current event for specific service.

        Args:
            request (twisted.web.server.Request): HTTP request object
            service_reference (basestring): Service reference string
        Returns:
            HTTP response with headers
        """
        data = dict(result=True, items=[],
                    service_reference=service_reference)
        data['items'] = self.ec.lookup(service_reference,
                                       querytype=QUERYTYPE_LOOKUP__WHILE,
                                       begin=QUERY_TIMESTAMP_CURRENT_TIME,
                                       minutes=0)
        return json_response(request, data)

    def render_list_item(self, request, service_reference, item_id):
        """
        Not supported

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        return self.error_response(request, response_code=http.NOT_FOUND)

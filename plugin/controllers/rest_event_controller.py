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
    RESTful Controller for /current_event endpoint.

    .. http:get:: /current_event

        :statuscode 200: no error
        :statuscode 404: no currently playing service

    .. http:get:: /current_event/{basestring:service_reference}/

        :statuscode 200: no error
        :statuscode 204: no data
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
            sr_obj = self.session.nav.getCurrentlyPlayingServiceReference()
            return self.render_list_subset(request, sr_obj.toString())
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
        items = self.ec.lookup(service_reference,
                               querytype=QUERYTYPE_LOOKUP__WHILE,
                               begin=QUERY_TIMESTAMP_CURRENT_TIME,
                               minutes=0)

        try:
            data = items[0]
            data["result"] = True
        except IndexError:
            data = dict(result=False,
                        service_reference=service_reference)
            request.setResponseCode(http.NO_CONTENT)

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

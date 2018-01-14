#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Timer Items
-----------

Listing of timer items on current device.
(Removing of timer items, Altering of timer items)
"""
import logging

from twisted.web import http

from rest import json_response
from rest import TwoFaceApiController, CORS_DEFAULT_ALLOW_ORIGIN
from timer import TimersController


class RESTTimerController(TwoFaceApiController):
    """
    RESTful Controller for ``/timers`` endpoint.

    .. http:get:: /timers/

        :statuscode 200: no error
        :statuscode 400: invalid

    .. http:get:: /timers/{basestring:service_reference}/

        :statuscode 200: no error
        :statuscode 400: invalid

    .. http:get:: /timers/{basestring:service_reference}/{int:timer_id}/

        :statuscode 200: no error
        :statuscode 400: invalid
        :statuscode 404: not found
    """
    def __init__(self, *args, **kwargs):
        TwoFaceApiController.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)
        self.session = kwargs.get("session")
        self.tc = TimersController(rt=self.session.nav.RecordTimer)

    def render_list_all(self, request):
        """
        List all timers

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        data = dict(result=True, items=[])

        for item in self.tc.list_items():
            data['items'].append(item)

        return json_response(request, data)

    def render_list_subset(self, request, service_reference):
        """
        List timers for specific service.

        Args:
            request (twisted.web.server.Request): HTTP request object
            service_reference (basestring): Service reference string
        Returns:
            HTTP response with headers
        """
        data = dict(result=True, items=[],
                    service_reference=service_reference)

        for item in self.tc.list_items(service_reference=service_reference):
            data['items'].append(item)

        return json_response(request, data)

    def render_list_item(self, request, service_reference, item_id):
        """
        List timer data for specific timer of service.

        Args:
            request (twisted.web.server.Request): HTTP request object
            service_reference (basestring): Service reference string
            item_id (int): Timer ID
        Returns:
            HTTP response with headers
        """
        data = dict(result=True, items=[],
                    service_reference=service_reference,
                    item_id=item_id)

        for item in self.tc.list_items(service_reference=service_reference,
                                       item_id=item_id):
            data['items'].append(item)

        if not data['items']:
            request.setResponseCode(http.NOT_FOUND)

        return json_response(request, data)

    def render_DELETE(self, request):
        """
        HTTP DELETE implementation for removing a timer.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers

        .. http:delete:: /timers/{basestring:service_reference}/{int:timer_id}/

            :statuscode 200: no error
            :statuscode 400: invalid
            :statuscode 404: not found
        """
        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        try:
            service_reference, item_id = self._mangle_args(request)
        except ValueError as vexc:
            item_id = None
            service_reference = None
            request.setResponseCode(http.BAD_REQUEST)
            self.log.error(vexc.message)

        try:
            self.tc.remove(service_reference, item_id)
        except ValueError as vexc:
            request.setResponseCode(http.BAD_REQUEST)
            self.log.error(vexc.message)

        data = {
            "result": False,
            "_controller": self.__class__.__name__,
            "request": {
                "postpath": request.postpath,
                "path": request.path,
                "args": request.args,
            }
        }

        return json_response(request, data)

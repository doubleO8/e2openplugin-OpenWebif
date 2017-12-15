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
from movie import MoviesController
from movie import mangle_servicereference
from events import QUERYTYPE_LOOKUP__WHILE, QUERY_TIMESTAMP_CURRENT_TIME


class RESTEventController(TwoFaceApiController):
    """
    RESTful Controller for /current_event endpoint.

    .. http:get:: /current_event

        :statuscode 200: no error
        :statuscode 503: no currently playing service

    .. http:get:: /current_event/{basestring:service_reference}/

        :statuscode 200: no error
        :statuscode 503: no data
    """

    def __init__(self, *args, **kwargs):
        TwoFaceApiController.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)
        self.session = kwargs.get("session")
        self.ec = EventsController()
        self.mc = MoviesController()

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
            servicereference = sr_obj.toString()
            item = mangle_servicereference(servicereference)
            self.log.info("sr item: {!r}".format(item))
            self.log.info("sr obj: {!r}".format(sr_obj.toString()))

            if item.get("path"):
                raw_data = self.mc.mangle_servicereference_information(sr_obj)
                if raw_data.get("event"):
                    data = raw_data.get("event")
                    data['service_reference'] = raw_data['meta'].get(
                        "Serviceref")
                else:
                    # do something ..
                    data = raw_data
                item.update(data)
                return json_response(request, item)
            return self.render_list_subset(request, sr_obj.toString())
        except Exception as exc:
            self.log.error(exc)
            self._cache(request, expires=False)
            return self.error_response(request,
                                       response_code=http.SERVICE_UNAVAILABLE)

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

        self._cache(request, expires=False)

        try:
            data = items[0]
            data["result"] = True
        except IndexError:
            data = dict(result=False,
                        service_reference=service_reference)
            request.setResponseCode(http.SERVICE_UNAVAILABLE)

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

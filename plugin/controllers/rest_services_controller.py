#!/usr/bin/env python
# -*- coding: utf-8 -*-
from twisted.web import http

from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton
from service import ServiceController
from utilities import add_expires_header


class RESTServicesController(RESTControllerSkeleton):
    """
    RESTful Controller for ``/services/`` endpoint
    """

    def __init__(self, *args, **kwargs):
        RESTControllerSkeleton.__init__(self, *args, **kwargs)
        self.sc_instance = ServiceController()

    def render_GET(self, request):
        """
        HTTP GET implementation.

        .. seealso::

            * *querytype* Parameter – :ref:`event_lookup_parameters-label`
            * *flags* Parameter – :ref:`event_format-label`

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers

        .. http:get:: /services/

            :statuscode 200: no error
            :statuscode 500: error(s)

        .. http:get:: /services/tv

            :statuscode 200: no error
            :statuscode 500: error(s)

        .. http:get:: /services/radio

            :statuscode 200: no error
            :statuscode 500: error(s)

        """
        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        data = {
            "errors": [],
            "len": 0,
            "postpath": request.postpath
        }

        service_types = None

        if len(request.postpath) == 0 or request.postpath[0] == '':
            service_types = None
        elif len(request.postpath) == 1:
            if request.postpath[0] in ('tv', 'radio'):
                service_types = request.postpath[0]

        try:
            data['services'] = list(self.sc_instance.get_services_set(
                service_types))
            data['result'] = True
            data['len'] = len(data['services'])
        except Exception as exc:
            data['errors'].append(repr(exc))
            request.setResponseCode(http.INTERNAL_SERVER_ERROR)

        add_expires_header(request, expires=14 * 24 * 3600)

        return json_response(request, data)

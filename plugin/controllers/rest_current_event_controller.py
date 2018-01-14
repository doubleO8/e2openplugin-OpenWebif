#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Current Event Data
------------------

Retrieve current event data.
"""
import logging

from twisted.web import http

import enigma
from rest import json_response
from rest import TwoFaceApiController
from events import EventsController
from recording import RecordingsController
from recording import mangle_servicereference
from events import QUERYTYPE_LOOKUP__WHILE, QUERY_TIMESTAMP_CURRENT_TIME
from models.model_utilities import mangle_epg_text
from models.events import KEY_SERVICE_REFERENCE, KEY_SERVICE_NAME
from models.events import NoneEventDict


def get_servicereference_name(some_ref):
    """
    Try to dertermine service's name for service reference *some_ref*

    Args:
        some_ref: eServiceReference instance or basestring
    Returns:
        service name or service reference string
    """
    ech = enigma.eServiceCenter.getInstance()

    try:
        if isinstance(some_ref, basestring):
            some_ref = enigma.eServiceReference(some_ref.encode("ascii"))
        sinfo = ech.info(some_ref)
        return mangle_epg_text(sinfo.getName(some_ref))
    except Exception:
        pass

    return str(some_ref)


class RESTCurrentEventController(TwoFaceApiController):
    """
    RESTful Controller for ``/current_event`` endpoint.

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
        self.mc = RecordingsController()

    def render_list_all(self, request):
        """
        Return event data for currently playing service.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        try:
            sr_obj = self.session.nav.getCurrentlyPlayingServiceReference()
            servicereference = sr_obj.toString()
            item = mangle_servicereference(servicereference)
            # self.log.debug("sr item: {!r}".format(item))
            # self.log.debug("sr obj: {!r}".format(sr_obj.toString()))

            if item.get("path"):
                raw_data = self.mc.mangle_servicereference_information(sr_obj)
                data = raw_data  # do something if no event data is available?

                if raw_data.get("event"):
                    data = raw_data.get("event")
                    data[KEY_SERVICE_REFERENCE] = raw_data['meta'].get(
                        "Serviceref")
                    data[KEY_SERVICE_NAME] = get_servicereference_name(
                        data[KEY_SERVICE_REFERENCE])
                else:
                    data = NoneEventDict(item.get("path").split('/')[-1])

                item.update(data)
                for key in ('kind', 'flags'):
                    try:
                        del item[key]
                    except KeyError:
                        pass

                return json_response(request, item)
            return self.render_list_subset(request, sr_obj.toString())
        except Exception as exc:
            self.log.error(exc)
            self._cache(request, expires=False)
            return self.error_response(request,
                                       response_code=http.SERVICE_UNAVAILABLE)

    def render_list_subset(self, request, service_reference):
        """
        Return event data for specific service (if available).

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
            data['path'] = None
        except IndexError:
            data = dict(service_reference=service_reference)
            request.setResponseCode(http.SERVICE_UNAVAILABLE)

        return json_response(request, data)

    def render_list_item(self, request, service_reference, item_id):
        """
        Currently not supported.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        return self.error_response(request, response_code=http.NOT_FOUND)

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
from rest import TwoFaceApiController


class RESTTimerController(TwoFaceApiController):
    """
    RESTful Controller for /timers endpoint.
    """
    def __init__(self, *args, **kwargs):
        TwoFaceApiController.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)
        self.session = kwargs.get("session")

    def render_list_all(self, request):
        data = dict(result=True, items=[])

        # override

        return json_response(request, data)

    def render_list_subset(self, request, service_reference):
        data = dict(result=True, items=[],
                    service_reference=service_reference)

        # override

        return json_response(request, data)

    def render_list_item(self, request, service_reference, item_id):
        data = dict(result=True, items=[],
                    service_reference=service_reference,
                    item_id=item_id)

        # override

        if not data['items']:
            request.setResponseCode(http.NOT_FOUND)

        return json_response(request, data)

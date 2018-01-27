#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Recordings
----------

Listing of recordings on current device.
Removing of recordings files including meta data.
"""
import os
import logging

from twisted.web import http

from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton
from recording import RecordingsController
from recording import RECORDINGS_ROOT_PATH, RECORDING_ENDPOINT_URL
from models.events import KEY_SERVICE_REFERENCE
from utilities import add_expires_header


class RESTRecordingsController(RESTControllerSkeleton):
    """
    RESTful Controller for ``/recordings`` endpoint.
    """
    def __init__(self, *args, **kwargs):
        RESTControllerSkeleton.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)
        self.movie_controller = RecordingsController()
        self.root = kwargs.get("root", RECORDINGS_ROOT_PATH)

    def render_path_listing(self, request, root_path):
        """
        Generate a list of movie items available on current device.

        Args:
            request (twisted.web.server.Request): HTTP request object
            root_path (basestring): Movie item to remove
        Returns:
            HTTP response with headers
        """
        data = dict(result=True, items=[])
        removed_keys = (KEY_SERVICE_REFERENCE, 'flags', 'kind',)
        r_path = request.path

        if r_path.endswith('/'):
            r_path = r_path[:-1]

        for item in self.movie_controller.list_movies(root_path):
            for rkey in removed_keys:
                try:
                    del item[rkey]
                except KeyError:
                    pass

            data["items"].append(item)
            if item["path"].startswith(self.root):
                item["path"] = '/'.join(
                    (r_path, item["path"][len(self.root):]))

        add_expires_header(request, expires=60*30)
        return json_response(request, data)

    def remove(self, request, target_path):
        """
        Remove movie file including meta data files.

        Args:
            request (twisted.web.server.Request): HTTP request object
            target_path (basestring): Movie item to remove
        Returns:
            HTTP response with headers
        """
        data = dict(files=[])
        e_ext_level1 = ('ts', 'eit',)
        e_ext_level2 = ('ap', 'cuts', 'meta', 'sc',)
        (trunk, _) = os.path.splitext(target_path)
        files_to_remove = []

        for ext1 in e_ext_level1:
            current = '.'.join((trunk, ext1))
            if os.path.isfile(current):
                files_to_remove.append(current)

        ext1 = e_ext_level1[0]
        for ext2 in e_ext_level2:
            current = '.'.join((trunk, ext1, ext2))
            if os.path.isfile(current):
                files_to_remove.append(current)

        for path in files_to_remove:
            try:
                os.unlink(path)
                data["files"].append(path)
            except Exception as exc:
                self.log.error(exc)

        return json_response(request, data)

    def render_GET(self, request):
        """
        HTTP GET request handler returning list of movies

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers

        .. http:get:: /recordings/{basestring:path}

            :statuscode 200: no error
            :statuscode 301: redirect
            :statuscode 404: not found

        .. http:get:: /recording/{basestring:path}

            :statuscode 200: no error
            :statuscode 404: not found
        """
        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        if len(request.postpath) == 0 or request.postpath[0] == '':
            target_path = self.root
        else:
            target_path = os.path.join(self.root,
                                       '/'.join(request.postpath))

        if os.path.isdir(target_path):
            return self.render_path_listing(request, target_path)
        elif os.path.isfile(target_path):
            url = RECORDING_ENDPOINT_URL + '/'.join(request.postpath)
            request.redirect(url)
            return ''

        return self.error_response(
            request, response_code=http.NOT_FOUND, message="not found")

    def render_DELETE(self, request):
        """
        HTTP DELETE request handler deleting a movie item

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers

        .. http:delete:: /recordings/{basestring:path}

            :statuscode 200: no error
            :statuscode 404: not found
        """
        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        target_path = os.path.join(self.root,
                                   '/'.join(request.postpath))

        if os.path.isfile(target_path):
            return self.remove(request, target_path)

        return self.error_response(request, message="not supported")

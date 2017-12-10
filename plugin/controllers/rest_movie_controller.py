#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import time
import datetime
import logging
from wsgiref.handlers import format_date_time

from twisted.web import http

from rest import json_response
from rest import CORS_DEFAULT_ALLOW_ORIGIN, RESTControllerSkeleton
from movie import MoviesController


class RESTMovieController(RESTControllerSkeleton):
    """
    RESTful Controller for /api/eventlookup endpoint
    """

    def __init__(self, *args, **kwargs):
        RESTControllerSkeleton.__init__(self, *args, **kwargs)
        self.log = logging.getLogger(__name__)
        self.movie_controller = MoviesController()
        self.root = kwargs.get("root", '/media/hdd/movie/')

    def _cache(self, request, expires=False):
        headers = {}
        if expires is False:
            headers[
                'Cache-Control'] = 'no-store, no-cache, must-revalidate, ' \
                                   'post-check=0, pre-check=0, max-age=0'
            headers['Expires'] = '-1'
        else:
            now = datetime.datetime.now()
            expires_time = now + datetime.timedelta(seconds=expires)
            headers['Cache-Control'] = 'public'
            headers['Expires'] = format_date_time(
                time.mktime(expires_time.timetuple()))
        for key in headers:
            self.log.debug(
                "CACHE: {key}={val}".format(key=key, val=headers[key]))
            request.setHeader(key, headers[key])

    def render_path_listing(self, request, root_path):
        data = dict(result=True, items=[])
        for item in self.movie_controller.list_movies(root_path):
            del item["servicereference"]
            del item["flags"]
            data["items"].append(item)
            if data["path"].startswith(self.root):
                data["path"] = data["path"][len(self.root):]

        if data["items"]:
            self._cache(request, expires=300)

        return json_response(request, data)

    def remove(self, request, target_path):
        data = dict(result=False)
        return json_response(request, data)

    def render_GET(self, request):
        """
        HTTP GET request handler returning list of movies

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
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

        return self.error_response(
            request, response_code=http.NOT_FOUND, message="not found")

    def render_DELETE(self, request):
        """
        HTTP DELETE request handler deleting a movie item

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        target_path = os.path.join(self.root,
                                   '/'.join(request.postpath))

        if os.path.isfile(target_path):
            return self.remove(request, target_path)

        return self.error_response(
            request, response_code=http.NOT_FOUND, message="not found")

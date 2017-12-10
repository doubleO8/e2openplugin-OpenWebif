#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

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
        self.movie_controller = MoviesController()

    def render_path_listing(self, request, root_path):
        data = dict(result=True, items=[])
        for item in self.movie_controller.list_movies(root_path):
            del item["servicereference"]
            del item["flags"]
            data["items"].append(item)
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
            target_path = '/media/hdd/movie'
        else:
            target_path = '/'.join(request.postpath)

        if os.path.isdir(target_path):
            return self.render_path_listing(request, target_path)

        return self.error_response(
            request, response_code=http.NOT_FOUND, message="not found")

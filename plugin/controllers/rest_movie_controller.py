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
    RESTful Controller for /movies endpoint
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
        removed_keys = ('servicereference', 'flags', 'kind',)
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

        if data["items"]:
            # self._cache(request, expires=30)
            self._cache(request)

        return json_response(request, data)

    def remove(self, request, target_path):
        data = dict(result=False)
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

        data["files"] = files_to_remove
        return json_response(request, data)

    def render_GET(self, request):
        """
        HTTP GET request handler returning list of movies

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers

        .. http:get:: /movies/{basestring:path}

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
            url = "/movie/" + '/'.join(request.postpath)
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

        .. http:delete:: /movies/{basestring:path}

            :statuscode 200: no error
            :statuscode 404: not found
        """
        request.setHeader(
            'Access-Control-Allow-Origin', CORS_DEFAULT_ALLOW_ORIGIN)

        target_path = os.path.join(self.root,
                                   '/'.join(request.postpath))

        if os.path.isfile(target_path):
            return self.remove(request, target_path)

        return self.error_response(
            request, response_code=http.NOT_FOUND, message="not found")

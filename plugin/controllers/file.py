# -*- coding: utf-8 -*-

##############################################################################
#                        2011 E2OpenPlugins                                  #
#                                                                            #
#  This file is open source software; you can redistribute it and/or modify  #
#     it under the terms of the GNU General Public License version 2 as      #
#               published by the Free Software Foundation.                   #
#                                                                            #
##############################################################################
import os
import glob
import json
import logging

from twisted.web import static, resource, http

from Components.config import config as comp_config
from utilities import require_valid_file_parameter, build_url
from utilities import mangle_host_header_port

def new_getRequestHostname(self):
    host = self.getHeader(b'host')
    if host:
        if host[0] == '[':
            return host.split(']', 1)[0] + "]"
        return host.split(':', 1)[0].encode('ascii')
    return self.getHost().host.encode('ascii')


http.Request.getRequestHostname = new_getRequestHostname

FLOG = logging.getLogger("filecrap")


class FileController(resource.Resource):
    def render(self, request):
        action = "download"
        if "action" in request.args:
            action = request.args["action"][0]

        if "file" in request.args:
            try:
                filename = require_valid_file_parameter(request, "file")
            except ValueError as verr:
                request.setResponseCode(http.BAD_REQUEST)
                FLOG.error(verr)
                return ''
            except IOError as ioerr:
                FLOG.error(ioerr)
                request.setResponseCode(http.NOT_FOUND)
                return ''

            if action == "stream":
                name = "stream"
                m3u_content = [
                    '#EXTM3U',
                    '#EXTVLCOPT--http-reconnect=true',
                ]

                if "name" in request.args:
                    name = request.args["name"][0]
                    m3u_content.append("#EXTINF:-1,%s" % name)

                mangled = mangle_host_header_port(
                    request.getHeader('host'),
                    fallback_port=comp_config.OpenWebif.port.value)
                args = {
                    "action": "download",
                    "file": filename
                }
                source_url = build_url(hostname=request.getRequestHostname(),
                                       path="file", args=args,
                                       port=mangled["port"])
                m3u_content.append(source_url)
                request.setHeader(
                    "Content-Disposition",
                    'attachment;filename="%s.m3u"' %
                    name)
                request.setHeader("Content-Type", "application/x-mpegurl")
                return "\n".join(m3u_content)
            elif action == "delete":
                request.setResponseCode(http.OK)
                return "TODO: DELETE FILE: %s" % (filename)
            elif action == "download":
                request.setHeader(
                    "Content-Disposition",
                    "attachment;filename=\"%s\"" % (filename.split('/')[-1]))
                rfile = static.File(
                    filename, defaultType="application/octet-stream")
                return rfile.render(request)
            else:
                return "wrong action parameter"

        if "dir" in request.args:
            path = request.args["dir"][0]
            pattern = '*'
            nofiles = False
            if "pattern" in request.args:
                pattern = request.args["pattern"][0]
            if "nofiles" in request.args:
                nofiles = True
            directories = []
            files = []
            request.setHeader(
                "content-type",
                "application/json; charset=utf-8")
            if os.path.isfile(path):
                if path == '/':
                    path = ''
                try:
                    files = glob.glob(path + '/' + pattern)
                except BaseException:
                    files = []
                files.sort()
                tmpfiles = files[:]
                for x in tmpfiles:
                    if os.path.isdir(x):
                        directories.append(x + '/')
                        files.remove(x)
                if nofiles:
                    files = []
                return json.dumps(
                    {"result": True, "dirs": directories, "files": files},
                    indent=2)
            else:
                return json.dumps(
                    {"result": False, "message": "path %s not exits" % (path)},
                    indent=2)

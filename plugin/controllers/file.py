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
import pprint

from twisted.web import static, resource, http

from Components.config import config as comp_config
from utilities import require_valid_file_parameter, build_url
from utilities import mangle_host_header_port
from base import CONTENT_TYPE_JSON
from defaults import FILE_ACCESS_WHITELIST
from recording import RECORDINGS_ROOT_PATH

FLOG = logging.getLogger("filecrap")


class FileController(resource.Resource):
    def render(self, request):
        action = "download"
        if "action" in request.args:
            action = request.args["action"][0]

        FLOG.warning("DEPRECATED file.py access:")
        FLOG.warning(pprint.pformat(request.args))

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

            if not filename.startswith(RECORDINGS_ROOT_PATH):
                if filename not in FILE_ACCESS_WHITELIST:
                    FLOG.error("{!r} NOT IN WHITELIST {!r}".format(filename, FILE_ACCESS_WHITELIST))
                    request.setResponseCode(http.FORBIDDEN)
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
                source_url = build_url(hostname=mangled['hostname'],
                                       path="file", args=args,
                                       port=mangled["port"])
                m3u_content.append(source_url)
                request.setHeader(
                    "Content-Disposition",
                    'attachment;filename="%s.m3u"' %
                    name)
                request.setHeader("Content-Type", "application/x-mpegurl")
                return "\n".join(m3u_content)
            elif action == "download":
                request.setHeader(
                    "Content-Disposition",
                    "attachment;filename=\"%s\"" % (filename.split('/')[-1]))
                rfile = static.File(
                    filename, defaultType="application/octet-stream")
                return rfile.render(request)
            else:
                FLOG.warning("Unsupported action: {!r}".format(action))
                request.setResponseCode(http.NOT_IMPLEMENTED)
                return ""

        if "dir" in request.args:
            FLOG.warning("No 'dir' support.")
            request.setResponseCode(http.NOT_IMPLEMENTED)
            return ""

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
                "content-type", CONTENT_TYPE_JSON)
            if os.path.isdir(path):
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

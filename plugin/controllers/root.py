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

from twisted.web import static
from twisted.web.resource import EncodingResourceWrapper
from twisted.web.server import GzipEncoderFactory

from models.info import getPublicPath, getPiconPath
from models.grab import grabScreenshot
from base import BaseController
from web import WebController
from ajax import AjaxController
from transcoding import TranscodingController
from file import FileController
import rest_fs_access
import rest_api_controller


class RootController(BaseController):
    def __init__(self, session, path=""):
        BaseController.__init__(self, path=path, session=session)
        piconpath = getPiconPath()
        publicpath = getPublicPath()

        self.putChild("web", WebController(session))
        api_controller_instance = EncodingResourceWrapper(
            rest_api_controller.ApiController(session, resource_prefix='/api'),
            [GzipEncoderFactory()])
        self.putChild("api", api_controller_instance)
        self.putChild("ajax", AjaxController(session))

        encoder_factory = rest_fs_access.GzipEncodeByFileExtensionFactory(
            extensions=[
                'txt', 'json', 'html', 'xml', 'js', 'conf', 'cfg',
                'eit', 'sc', 'ap'
            ])

        #: gzip compression enabled file controller
        wrapped_fs_controller = EncodingResourceWrapper(
            rest_fs_access.RESTFilesystemController(
                root='/',
                resource_prefix="/fs",
                session=session),
            [encoder_factory]
        )
        self.putChild("fs", wrapped_fs_controller)

        self.putChild("file", FileController())
        self.putChild("grab", grabScreenshot(session))
        self.putChild("js", static.File(publicpath + "/js"))
        self.putChild("css", static.File(publicpath + "/css"))
        self.putChild("static", static.File(publicpath + "/static"))
        self.putChild("images", static.File(publicpath + "/images"))
        self.putChild("fonts", static.File(publicpath + "/fonts"))
        if os.path.exists(getPublicPath('themes')):
            self.putChild("themes", static.File(publicpath + "/themes"))
        self.putChild("transcoding", TranscodingController())
        if piconpath:
            self.putChild("picon", static.File(piconpath))

    # this function will be called before a page is loaded
    def prePageLoad(self, request):
        # we set withMainTemplate here so it's a default for every page
        self.withMainTemplate = True

    # the "pages functions" must be called P_pagename
    # example http://boxip/index => P_index
    def P_index(self, request):
        return {}

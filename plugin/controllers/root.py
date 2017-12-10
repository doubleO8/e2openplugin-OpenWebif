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

from Plugins.Extensions.OpenWebif.__init__ import _
from enigma import eEPGCache
from models.config import getCollapsedMenus, getConfigsSections
from models.config import getShowName, getCustomName, getBoxName

from models.info import getPublicPath, getPiconPath, getInfo
from models.grab import grabScreenshot
from base import BaseController
from web import WebController
from ajax import AjaxController
from transcoding import TranscodingController
from file import FileController
import rest_fs_access
import rest_api_controller
import rest_movie_controller

try:
    from boxbranding import getBoxType
except BaseException:
    from models.owibranding import getBoxType


class RootController(BaseController):
    """
    Web root controller.
    """

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

        movie_controller_instanc = EncodingResourceWrapper(
            rest_movie_controller.RESTMovieController(),
            [GzipEncoderFactory()])
        self.putChild("movies", movie_controller_instanc)
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

    def P_index(self, request):
        """
        The "pages functions" must be called `P_<pagename>`.

        Example:
            Contents for endpoint `/index` will be generated using a method
            named `P_index`.

        Args:
            request (twisted.web.server.Request): HTTP request object

        Returns:
            dict: Parameter values
        """
        ret = getCollapsedMenus()
        ginfo = getInfo()
        ret['configsections'] = getConfigsSections()['sections']
        ret['showname'] = getShowName()['showname']
        ret['customname'] = getCustomName()['customname']
        ret['boxname'] = getBoxName()['boxname']

        if not ret['boxname'] or not ret['customname']:
            ret['boxname'] = ginfo['brand'] + " " + ginfo['model']
        ret['box'] = getBoxType()

        if hasattr(eEPGCache, 'FULL_DESCRIPTION_SEARCH'):
            ret['epgsearchcaps'] = True
        else:
            ret['epgsearchcaps'] = False

        ret['extras'] = [
            {'key': 'ajax/settings', 'description': _("Settings")}
        ]
        ret['theme'] = 'original-small-screen'
        ret['content'] = ''
        return ret

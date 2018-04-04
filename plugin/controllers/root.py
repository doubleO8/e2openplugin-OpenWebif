# -*- coding: utf-8 -*-

##############################################################################
#                        2011 E2OpenPlugins                                  #
#                                                                            #
#  This file is open source software; you can redistribute it and/or modify  #
#     it under the terms of the GNU General Public License version 2 as      #
#               published by the Free Software Foundation.                   #
#                                                                            #
##############################################################################
from twisted.web import static
from twisted.web.resource import EncodingResourceWrapper
from twisted.web.server import GzipEncoderFactory

from i18n import _
from defaults import PUBLIC_PATH, PICON_PATH, FAVICON_PATH

from enigma import eEPGCache
from models.config import getCollapsedMenus, getConfigsSections
from models.config import getShowName, getCustomName, getBoxName
from models.info import getInfo
from models.grab import grabScreenshot
from base import BaseController
from web import WebController
from transcoding import TranscodingController
from file import FileController
import rest_api_controller
import rest_recordings_controller
import rest_timer_controller
import rest_current_event_controller
import rest_services_controller
from recording import RECORDINGS_ROOT_PATH
from recording import RECORDINGS_ENDPOINT_PATH, RECORDING_ENDPOINT_PATH

TOW_FRONTEND = False

try:
    from ajax import AjaxController
    TOW_FRONTEND = True
except ImportError:
    pass

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

        self.putChild("web", WebController(session))
        api_controller_instance = EncodingResourceWrapper(
            rest_api_controller.ApiController(session, resource_prefix='/api'),
            [GzipEncoderFactory()])
        self.putChild("api", api_controller_instance)

        recordings_controller_instance = EncodingResourceWrapper(
            rest_recordings_controller.RESTRecordingsController(),
            [GzipEncoderFactory()])
        self.putChild(RECORDINGS_ENDPOINT_PATH,
                      recordings_controller_instance)
        self.putChild(RECORDING_ENDPOINT_PATH,
                      static.File(RECORDINGS_ROOT_PATH))

        timer_controller_instance = EncodingResourceWrapper(
            rest_timer_controller.RESTTimerController(session=session),
            [GzipEncoderFactory()])
        self.putChild("timers", timer_controller_instance)

        services_controller_instance = EncodingResourceWrapper(
            rest_services_controller.RESTServicesController(),
            [GzipEncoderFactory()])
        self.putChild("services", services_controller_instance)

        event_controller_instance = EncodingResourceWrapper(
            rest_current_event_controller.RESTCurrentEventController(
                session=session), [GzipEncoderFactory()])
        self.putChild("current_event", event_controller_instance)

        self.putChild("file", FileController())
        self.putChild("grab", grabScreenshot(session))

        if TOW_FRONTEND:
            self.putChild("ajax", AjaxController(session))
            self.putChild('favicon.ico', static.File(FAVICON_PATH))
            self.putChild('favicon.png', static.File(FAVICON_PATH))

        for shortcut in ('js', 'css', 'static', 'images', 'fonts'):
            self.putChild(shortcut,
                          static.File('/'.join((PUBLIC_PATH, shortcut))))

        self.putChild("transcoding", TranscodingController())
        if PICON_PATH:
            self.putChild("picon", static.File(PICON_PATH))

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

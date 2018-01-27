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
import logging
from socket import has_ipv6

from Components.config import config as comp_config
from controllers.root import RootController

from twisted.internet import reactor
from twisted.web import server, version
from twisted.internet.error import CannotListenError

HLOG = logging.getLogger('httpserver')

global listener, server_to_stop, site
listener = []


def HttpdStart(session):
    """
    Helper class to start web server

    Args:
        session: (?) session object
    """
    if comp_config.OpenWebif.enabled.value:
        global listener, site
        port = comp_config.OpenWebif.port.value

        root = RootController(session)
        site = server.Site(root)

        ipv6_interface = os.path.isfile('/proc/net/if_inet6')
        # start http webserver on configured port
        try:
            if has_ipv6 and ipv6_interface and version.major >= 12:
                # use ipv6
                listener.append(reactor.listenTCP(port, site, interface='::'))
            else:
                # ipv4 only
                listener.append(reactor.listenTCP(port, site))
            HLOG.debug("started listening on {:d}".format(port))
        except CannotListenError as cle:
            HLOG.warning("failed to listen on Port {:d}: {!r}".format(
                port, cle))

        # Streaming requires listening on 127.0.0.1:80
        if port != 80:
            try:
                if has_ipv6 and ipv6_interface and version.major >= 12:
                    # use ipv6
                    listener.append(
                        reactor.listenTCP(80, site, interface='::1'))
                    listener.append(
                        reactor.listenTCP(
                            80, site, interface='::ffff:127.0.0.1'))
                else:
                    # ipv4 only
                    listener.append(
                        reactor.listenTCP(
                            80, site, interface='127.0.0.1'))
                HLOG.debug("started stream listening on port 80")
            except CannotListenError as cle2:
                HLOG.warning("port 80 busy: {!r}".format(cle2))


def HttpdStop(session):
    StopServer(session).doStop()


def HttpdRestart(session):
    StopServer(session, HttpdStart).doStop()


class StopServer:
    """
    Helper class to stop running web servers; we use a class here to reduce use
    of global variables. Resembles code prior found in HttpdStop et. al.
    """
    server_to_stop = 0

    def __init__(self, session, callback=None):
        self.session = session
        self.callback = callback

    def doStop(self):
        global listener
        self.server_to_stop = 0
        for interface in listener:
            HLOG.debug("Stopping server on port {!r}".format(interface.port))
            deferred = interface.stopListening()
            try:
                self.server_to_stop += 1
                deferred.addCallback(self.callbackStopped)
            except AttributeError:
                pass
        listener = []
        if self.server_to_stop < 1:
            self.doCallback()

    def callbackStopped(self, reason):
        self.server_to_stop -= 1
        if self.server_to_stop < 1:
            self.doCallback()

    def doCallback(self):
        if self.callback is not None:
            self.callback(self.session)

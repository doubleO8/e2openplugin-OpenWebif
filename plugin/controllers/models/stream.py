# -*- coding: utf-8 -*-

##############################################################################
#                        2011 E2OpenPlugins                                  #
#                                                                            #
#  This file is open source software; you can redistribute it and/or modify  #
#     it under the terms of the GNU General Public License version 2 as      #
#               published by the Free Software Foundation.                   #
#                                                                            #
##############################################################################
import urllib
import urlparse
import os
import re

from enigma import eServiceReference, getBestPlayableServiceReference
from ServiceReference import ServiceReference
from Components.config import config
from info import getInfo


MODEL_TRANSCODING = (
    "Uno4K",
    "Ultimo4K",
    "Solo4K",
    "Solo²",
    "Duo²",
    "Solo SE",
    "Quad",
    "Quad Plus",
)

MACHINEBUILD_TRANSCODING = (
    'dags7356',
    'dags7252',
    'gb7252',
    'gb7356',
)

MACHINEBUILD_TRANSCODING_DYNAMIC = (
    'inihdp',
    'hd2400',
    'et10000',
    'et13000',
    'sf5008',
    '8100s',
)

MACHINEBUILD_TRANSCODING_NORMAL = (
    'ew7356',
    'formuler1tc',
    'tiviaraplus'
)

MACHINEBUILD_TRANSCODING_ANY = MACHINEBUILD_TRANSCODING_DYNAMIC + \
                               MACHINEBUILD_TRANSCODING_NORMAL


def build_url(hostname, path, args, scheme="http", port=None):
    """
    Create an URL based on parameters.

    Args:
        hostname: hostname portion
        path: path portion
        args: query parameters
        scheme: scheme portion
        port: port portion

    Returns:
        basestring: Generated URL
    """
    netloc = hostname
    if port:
        netloc = '{:s}:{!s}'.format(hostname, port)
    path_q = urllib.quote(path)
    args_e = urllib.urlencode(args)
    return urlparse.urlunparse((scheme, netloc, path_q, None, args_e, None))


def create_transcoding_args(machinebuild, for_phone):
    """
    Create transcoding query parameters `dict` based on *machine build* and
    *is mobile device* option.

    Args:
        machinebuild: machine build indicator
        for_phone: for mobile device indicator

    Returns:
        dict: query parameters
    """
    args = dict()
    if not for_phone:
        return args

    if machinebuild in MACHINEBUILD_TRANSCODING_DYNAMIC:
        args = dict(
            bitrate=config.plugins.transcodingsetup.bitrate.value,
            resolution=config.plugins.transcodingsetup.resolution.value,
            aspectratio=config.plugins.transcodingsetup.aspectratio.value,
            interlaced=config.plugins.transcodingsetup.interlaced.value,
        )
        (args['width'], args['height']) = args['resolution'].split('x')
    elif machinebuild in MACHINEBUILD_TRANSCODING_NORMAL:
        args = dict(
            bitrate=config.plugins.transcodingsetup.bitrate.value
        )

    return args


def create_stream_m3u(session, request, m3ufile):
    """
    Create M3U contents for service streaming.

    Args:
        session: enigma session object
        request (twisted.web.server.Request): HTTP request object
        m3ufile: M3U filename

    Returns:
        M3U contents
    """
    progopt = ''
    sRef = ""
    currentServiceRef = None

    if "ref" in request.args:
        sRef = request.args["ref"][0].decode('utf-8', 'ignore').encode('utf-8')

    for_phone = False
    if "device" in request.args:
        for_phone = request.args["device"][0] == "phone"

    if m3ufile == "streamcurrent.m3u":
        currentServiceRef = session.nav.getCurrentlyPlayingServiceReference()
        sRef = currentServiceRef.toString()

    if sRef.startswith("1:134:"):
        if currentServiceRef is None:
            currentServiceRef = session.nav.getCurrentlyPlayingServiceReference()  # NOQA
        if currentServiceRef is None:
            currentServiceRef = eServiceReference()
        ref = getBestPlayableServiceReference(
            eServiceReference(sRef), currentServiceRef)
        if ref is None:
            sRef = ""
        else:
            sRef = ref.toString()

    portNumber = config.OpenWebif.streamport.value
    info = getInfo()
    model = info["model"]
    machinebuild = info["machinebuild"]
    transcoder_port = None
    args = create_transcoding_args(machinebuild, for_phone)

    if model in MODEL_TRANSCODING or machinebuild in MACHINEBUILD_TRANSCODING:
        try:
            transcoder_port = int(config.plugins.transcodingsetup.port.value)
        except Exception:
            # Transcoding Plugin is not installed or your STB does not support
            # transcoding
            pass
        if for_phone:
            portNumber = transcoder_port
        if "port" in request.args:
            portNumber = request.args["port"][0]

    # INI use dynamic encoder allocation, and each stream can have diffrent
    # parameters
    if machinebuild in MACHINEBUILD_TRANSCODING_ANY:
        transcoder_port = 8001

    if config.OpenWebif.service_name_for_stream.value:
        # #EXTINF:-1,%s\n adding back to show service name in programs like VLC
        if "name" in request.args:
            name = request.args["name"][0]
            progopt = "#EXTINF:-1,%s\n" % name

        # When you use EXTVLCOPT:program in a transcoded stream, VLC does
        # not play stream
        if sRef != '' and portNumber != transcoder_port:
            progopt += "#EXTVLCOPT:program=%d\n" % (
                int(sRef.split(':')[3], 16))

    response = "#EXTM3U \n#EXTVLCOPT--http-reconnect=true \n%s%s\n" % (
        progopt, build_url(hostname=request.getRequestHostname(),
                           port=portNumber, path=sRef, args=args))
    request.setHeader('Content-Type', 'application/x-mpegurl')
    return response


def create_file_m3u(request):
    """
    Create M3U contents for file streaming.

    Args:
        request (twisted.web.server.Request): HTTP request object

    Returns:
        M3U contents
    """
    if "file" not in request.args:
        return "Missing file parameter"

    filename = request.args["file"][0].decode(
        'utf-8', 'ignore').encode('utf-8')

    if not os.path.exists(filename):
        return "File '%s' not found" % (filename)

    for_phone = False
    if "device" in request.args:
        for_phone = request.args["device"][0] == "phone"

    # ServiceReference is not part of filename so look in
    # the '.ts.meta' file
    sRef = ""
    progopt = ''

    if config.OpenWebif.service_name_for_stream.value:
        metafilename = filename + '.meta'
        try:
            with open(metafilename, "rb") as src:
                lines = [x.strip() for x in src.readlines()]
                name = ''
                seconds = -1  # unknown duration default
                if lines[0]:  # service ref
                    sRef = eServiceReference(lines[0]).toString()
                if lines[1]:  # name
                    name = lines[1]
                if lines[5]:  # length
                    seconds = float(lines[5]) / 90000  # In seconds
                progopt += "#EXTINF:%d,%s\n" % (seconds, name)
        except (IOError, ValueError, IndexError):
            pass

    portNumber = None
    info = getInfo()
    model = info["model"]
    machinebuild = info["machinebuild"]
    transcoder_port = None

    # INI use dynamic encoder allocation, and each stream can have
    # different parameters
    args = create_transcoding_args(machinebuild, for_phone)

    if model in MODEL_TRANSCODING or machinebuild in MACHINEBUILD_TRANSCODING:
        try:
            transcoder_port = int(config.plugins.transcodingsetup.port.value)
        except Exception:
            # Transcoding Plugin is not installed or your STB does not
            # support transcoding
            pass

        if for_phone:
            portNumber = transcoder_port

    if "port" in request.args:
        portNumber = request.args["port"][0]

    if for_phone:
        if machinebuild in MACHINEBUILD_TRANSCODING_ANY:
            portNumber = config.OpenWebif.streamport.value

    # When you use EXTVLCOPT:program in a transcoded stream, VLC does not
    # play stream
    use_s_name = config.OpenWebif.service_name_for_stream.value
    if use_s_name and sRef != '' and portNumber != transcoder_port:
        progopt += "#EXTVLCOPT:program=%d\n" % (int(sRef.split(':')[3], 16))

    if portNumber is None:
        portNumber = config.OpenWebif.port.value
        ourhost = request.getHeader('host')
        m = re.match('.+\:(\d+)$', ourhost)
        if m is not None:
            portNumber = m.group(1)

    args['file'] = filename
    response = "#EXTM3U \n#EXTVLCOPT--http-reconnect=true \n%s%s\n" % (
        (progopt, build_url(
            hostname=request.getRequestHostname(),
            port=portNumber, path="file", args=args)))
    request.setHeader('Content-Type', 'application/x-mpegurl')
    return response


def getStreamSubservices(session, request):
    services = []
    currentServiceRef = session.nav.getCurrentlyPlayingServiceReference()

    # TODO : this will only work if sref = current channel
    # the DMM webif can also show subservices for other channels
    # like the current ideas are welcome

    if "sRef" in request.args:
        currentServiceRef = eServiceReference(request.args["sRef"][0])

    if currentServiceRef is not None:
        currentService = session.nav.getCurrentService()
        subservices = currentService.subServices()

        services.append({
            "servicereference": currentServiceRef.toString(),
            "servicename": ServiceReference(currentServiceRef).getServiceName()
        })
        if subservices and subservices.getNumberOfSubservices() != 0:
            n = subservices and subservices.getNumberOfSubservices()
            z = 0
            while z < n:
                sub = subservices.getSubservice(z)
                services.append({
                    "servicereference": sub.toString(),
                    "servicename": sub.getName()
                })
                z += 1
    else:
        services.append = ({
            "servicereference": "N/A",
            "servicename": "N/A"
        })

    return {"services": services}

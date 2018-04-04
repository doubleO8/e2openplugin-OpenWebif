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
import time
from time import mktime, localtime, strftime
from collections import OrderedDict
from urllib import quote, unquote

from Components.config import config as comp_config
from Components.NimManager import nimmanager
from Screens.ChannelSelection import service_types_tv, service_types_radio
from enigma import eServiceCenter, eServiceReference, \
    iServiceInformation, eEPGCache

from i18n import _
from defaults import THEMES
from utilities import parse_servicereference, SERVICE_TYPE_LOOKUP, NS_LOOKUP

from models.model_utilities import mangle_epg_text
from models.services import getPicon
from models.services import getBouquets, getSatellites, \
    getChannelEpg, getSearchEpg, getEvent, \
    getCurrentService, getServiceInfoString
from models.info import getOrbitalText
from models.info import getInfo, getTranscodingSupport, \
    getLanguage, getStatusInfo
from models.movies import getMovieList
from models.timers import getTimers
from models.config import getConfigs, getConfigsSections, getZapStream, \
    getShowChPicon, addCollapsedMenu, removeCollapsedMenu
from base import BaseController

try:
    from boxbranding import getMachineBrand
except BaseException:
    from models.owibranding import getMachineBrand


def getMultiEpg(self, ref, begintime=-1, endtime=None, Mode=1):
    # Check if an event has an associated timer. Unfortunately
    # we cannot simply check against timer.eit, because a timer
    # does not necessarily have one belonging to an epg event id.
    def getTimerEventStatus(event):
        startTime = event[1]
        endTime = event[1] + event[6] - 120
        serviceref = event[4]
        if serviceref not in timerlist:
            return ''
        for timer in timerlist[serviceref]:
            if timer.begin <= startTime and timer.end >= endTime:
                if timer.disabled:
                    return 'timer disabled'
                else:
                    return 'timer'
        return ''

    ret = OrderedDict()
    services = eServiceCenter.getInstance().list(eServiceReference(ref))
    if not services:
        return {"events": ret, "result": False, "slot": None}

    search = ['IBTSRND']
    for service in services.getContent('S'):
        if endtime:
            search.append((service, 0, begintime, endtime))
        else:
            search.append((service, 0, begintime))

    epgcache = eEPGCache.getInstance()
    events = epgcache.lookupEvent(search)
    offset = None
    picons = {}

    if events is not None:
        # We want to display if an event is covered by a timer.
        # To keep the costs low for a nested loop against the timer list, we
        # partition the timers by service reference. For an event we then only
        # have to check the part of the timers that belong to that specific
        # service reference. Partition is generated here.
        timerlist = {}
        for timer in self.session.nav.RecordTimer.timer_list + \
                self.session.nav.RecordTimer.processed_timers:
            if str(timer.service_ref) not in timerlist:
                timerlist[str(timer.service_ref)] = []
            timerlist[str(timer.service_ref)].append(timer)

        if begintime == -1:
            # If no start time is requested, use current time as start time
            # and extend show all events until 6:00 next day
            bt = localtime()
            offset = mktime(
                (bt.tm_year, bt.tm_mon, bt.tm_mday, bt.tm_hour - bt.tm_hour %
                 2, 0, 0, -1, -1, -1))
            lastevent = mktime(
                (bt.tm_year, bt.tm_mon, bt.tm_mday, 23, 59, 0, -1, -1,
                 -1)) + 6 * 3600
        else:
            # If a start time is requested, show all events in a 24 hour frame
            bt = localtime(begintime)
            offset = mktime(
                (bt.tm_year, bt.tm_mon, bt.tm_mday, bt.tm_hour - bt.tm_hour %
                 2, 0, 0, -1, -1, -1))
            lastevent = offset + 86399

        for event in events:
            ev = {}
            ev['id'] = event[0]
            ev['begin_timestamp'] = event[1]
            ev['title'] = event[2]
            ev['shortdesc'] = event[3]
            ev['ref'] = event[4]
            ev['timerStatus'] = getTimerEventStatus(event)
            if Mode == 2:
                ev['duration'] = event[6]

            channel = mangle_epg_text(event[5])
            if channel not in ret:
                if Mode == 1:
                    ret[channel] = [[], [], [], [],
                                    [], [], [], [], [], [], [], []]
                else:
                    ret[channel] = [[]]
                picons[channel] = getPicon(event[4])

            if Mode == 1:
                slot = int((event[1] - offset) / 7200)
                if slot < 0:
                    slot = 0
                if slot < 12 and event[1] < lastevent:
                    ret[channel][slot].append(ev)
            else:
                ret[channel][0].append(ev)
    return {"events": ret, "result": True, "picons": picons}


def getCurrentFullInfo(session):
    now = next = {}
    inf = getCurrentService(session)
    inf['tuners'] = list(map(chr, range(65, 65 + nimmanager.getSlotCount())))

    try:
        info = session.nav.getCurrentService().info()
    except BaseException:
        info = None

    try:
        subservices = session.nav.getCurrentService().subServices()
    except BaseException:
        subservices = None

    try:
        audio = session.nav.getCurrentService().audioTracks()
    except BaseException:
        audio = None

    try:
        ref = session.nav.getCurrentlyPlayingServiceReference().toString()
    except BaseException:
        ref = None

    if ref is not None:
        inf['sref'] = '_'.join(ref.split(':', 10)[:10])
        inf['srefv2'] = ref
        inf['picon'] = getPicon(ref)
        inf['wide'] = inf['aspect'] in (3, 4, 7, 8, 0xB, 0xC, 0xF, 0x10)
        inf['ttext'] = getServiceInfoString(info, iServiceInformation.sTXTPID)
        inf['crypt'] = getServiceInfoString(
            info, iServiceInformation.sIsCrypted)
        inf['subs'] = str(
            subservices and subservices.getNumberOfSubservices() > 0)
    else:
        inf['sref'] = None
        inf['picon'] = None
        inf['wide'] = None
        inf['ttext'] = None
        inf['crypt'] = None
        inf['subs'] = None

    inf['date'] = strftime("%d.%m.%Y", (localtime()))
    inf['dolby'] = False

    if audio:
        n = audio.getNumberOfTracks()
        idx = 0
        while idx < n:
            i = audio.getTrackInfo(idx)
            description = i.getDescription()
            if "AC3" in description \
                    or "DTS" in description \
                    or "Dolby Digital" in description:
                inf['dolby'] = True
            idx += 1
    try:
        feinfo = session.nav.getCurrentService().frontendInfo()
    except BaseException:
        feinfo = None

    frontendData = feinfo and feinfo.getAll(True)

    if frontendData is not None:
        cur_info = feinfo.getTransponderData(True)
        inf['tunertype'] = frontendData.get("tuner_type", "UNKNOWN")
        if frontendData.get("system", -1) == 1:
            inf['tunertype'] = "DVB-S2"
        inf['tunernumber'] = frontendData.get("tuner_number")
        orb = getOrbitalText(cur_info)
        inf['orbital_position'] = orb
        if cur_info:
            if cur_info.get('tuner_type') == "DVB-S":
                inf['orbital_position'] = _("Orbital Position") + ': ' + orb
    else:
        inf['tunernumber'] = "N/A"
        inf['tunertype'] = "N/A"

    try:
        frontendStatus = feinfo and feinfo.getFrontendStatus()
    except BaseException:
        frontendStatus = None

    if frontendStatus is not None:
        percent = frontendStatus.get("tuner_signal_quality")
        if percent is not None:
            inf['snr'] = int(percent * 100 / 65535)
            inf['snr_db'] = inf['snr']
        percent = frontendStatus.get("tuner_signal_quality_db")
        if percent is not None:
            inf['snr_db'] = "%3.02f dB" % (percent / 100.0)
        percent = frontendStatus.get("tuner_signal_power")
        if percent is not None:
            inf['agc'] = int(percent * 100 / 65535)
        percent = frontendStatus.get("tuner_bit_error_rate")
        if percent is not None:
            inf['ber'] = int(percent * 100 / 65535)
    else:
        inf['snr'] = 0
        inf['snr_db'] = inf['snr']
        inf['agc'] = 0
        inf['ber'] = 0

    try:
        recordings = session.nav.getRecordings()
    except BaseException:
        recordings = None

    inf['rec_state'] = False
    if recordings:
        inf['rec_state'] = True

    ev = getChannelEpg(ref)
    if len(ev['events']) > 1:
        now = ev['events'][0]
        next = ev['events'][1]
        if len(now['title']) > 50:
            now['title'] = now['title'][0:48] + "..."
        if len(next['title']) > 50:
            next['title'] = next['title'][0:48] + "..."

    return {"info": inf, "now": now, "next": next}


def getProviders(stype):
    s_type = service_types_tv
    if stype == "radio":
        s_type = service_types_radio
    serviceHandler = eServiceCenter.getInstance()
    services = serviceHandler.list(
        eServiceReference(
            '%s FROM PROVIDERS ORDER BY name' %
            (s_type)))
    providers = services and services.getContent("SN", True)
    return {"providers": providers}


def getEventDesc(ref, idev):
    ref = unquote(ref)
    epgcache = eEPGCache.getInstance()
    event = epgcache.lookupEvent(['ESX', (ref, 2, int(idev))])
    if len(event[0][0]) > 1:
        description = mangle_epg_text(event[0][0])
    elif len(event[0][1]) > 1:
        description = mangle_epg_text(event[0][1])
    else:
        description = "No description available"

    return {"description": description}


def getChannels(idbouquet, stype):
    ret = []
    idp = 0
    s_type = service_types_tv
    if stype == "radio":
        s_type = service_types_radio
    if idbouquet == "ALL":
        idbouquet = '%s ORDER BY name' % (s_type)

    epgcache = eEPGCache.getInstance()
    serviceHandler = eServiceCenter.getInstance()
    services = serviceHandler.list(eServiceReference(idbouquet))
    channels = services and services.getContent("SN", True)
    for channel in channels:
        chan = {}
        chan['ref'] = quote(channel[0], safe=' ~@%#$&()*!+=:;,.?/\'')
        if chan['ref'].split(":")[1] == '320':  # Hide hidden number markers
            continue
        chan['name'] = mangle_epg_text(channel[1])
        if not int(channel[0].split(":")[1]) & 64:
            psref = parse_servicereference(channel[0])
            chan['service_type'] = SERVICE_TYPE_LOOKUP.get(
                psref.get('service_type'), "UNKNOWN")
            chan['ns'] = NS_LOOKUP.get(psref.get('ns'), "DVB-S")
            chan['picon'] = getPicon(chan['ref'])
            chan['protection'] = "0"
            nowevent = epgcache.lookupEvent(['TBDCIX', (channel[0], 0, -1)])
            if len(nowevent) > 0 and nowevent[0][0] is not None:
                chan['now_title'] = mangle_epg_text(nowevent[0][0])
                chan['now_begin'] = strftime(
                    "%H:%M", (localtime(nowevent[0][1])))
                chan['now_end'] = strftime(
                    "%H:%M", (localtime(nowevent[0][1] + nowevent[0][2])))
                chan['now_left'] = int(
                    ((nowevent[0][1] + nowevent[0][2]) - nowevent[0][3]) / 60)
                chan['progress'] = int(
                    ((nowevent[0][3] - nowevent[0][1]) * 100 / nowevent[0][2]))
                chan['now_ev_id'] = nowevent[0][4]
                chan['now_idp'] = "nowd" + str(idp)
                nextevent = epgcache.lookupEvent(
                    ['TBDIX', (channel[0], +1, -1)])
                if len(nextevent) > 0 and nextevent[0][0] is not None:
                    # Some fields have been seen to be missing from the next
                    # event...
                    if nextevent[0][1] is None:
                        nextevent[0][1] == time.time()
                    if nextevent[0][2] is None:
                        nextevent[0][2] == 0
                    chan['next_title'] = mangle_epg_text(nextevent[0][0])
                    chan['next_begin'] = strftime(
                        "%H:%M", (localtime(nextevent[0][1])))
                    chan['next_end'] = strftime(
                        "%H:%M", (
                            localtime(nextevent[0][1] + nextevent[0][2])))
                    chan['next_duration'] = int(nextevent[0][2] / 60)
                    chan['next_ev_id'] = nextevent[0][3]
                    chan['next_idp'] = "nextd" + str(idp)
                else:
                    # Have to fudge one in, as rest of OWI code expects it...
                    chan['next_title'] = mangle_epg_text("<<absent>>")
                    chan['next_begin'] = chan['now_end']
                    chan['next_end'] = chan['now_end']
                    chan['next_duration'] = 0
                    chan['next_ev_id'] = chan['now_ev_id']
                    chan['next_idp'] = chan['now_idp']
                idp += 1
        if int(channel[0].split(":")[1]) != 832:
            ret.append(chan)
    return {"channels": ret}


class AjaxController(BaseController):
    """
    Helper controller class for AJAX requests.
    """

    def __init__(self, session, path=""):
        BaseController.__init__(self, path=path, session=session)

    def testMandatoryArguments(self, request, keys):
        for key in keys:
            if key not in request.args.keys():
                return {
                    "result": False,
                    "message": _("Missing mandatory parameter '%s'") % key
                }

            if len(request.args[key][0]) == 0:
                return {
                    "result": False,
                    "message": _("The parameter '%s' can't be empty") % key
                }

        return None

    def P_current(self, request):
        return getCurrentFullInfo(self.session)

    def P_bouquets(self, request):
        """
        Gather information about available bouquets.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            dict: key/value pairs
        """
        stype = "tv"
        if "stype" in request.args.keys():
            stype = request.args["stype"][0]
        bouq = getBouquets(stype)
        return {"bouquets": bouq['bouquets'], "stype": stype}

    def P_providers(self, request):
        stype = "tv"
        if "stype" in request.args.keys():
            stype = request.args["stype"][0]
        prov = getProviders(stype)
        return {"providers": prov['providers'], "stype": stype}

    def P_satellites(self, request):
        stype = "tv"
        if "stype" in request.args.keys():
            stype = request.args["stype"][0]
        sat = getSatellites(stype)
        return {"satellites": sat['satellites'], "stype": stype}

    def P_channels(self, request):
        stype = "tv"
        idbouquet = "ALL"
        if "stype" in request.args.keys():
            stype = request.args["stype"][0]
        if "id" in request.args.keys():
            idbouquet = request.args["id"][0]
        channels = getChannels(idbouquet, stype)
        channels['transcoding'] = getTranscodingSupport()
        channels['type'] = stype
        channels['showchannelpicon'] = getShowChPicon()['showchannelpicon']
        return channels

    def P_eventdescription(self, request):
        return getEventDesc(request.args["sref"][0], request.args["idev"][0])

    def P_event(self, request):
        margin_before = comp_config.recording.margin_before.value
        margin_after = comp_config.recording.margin_after.value
        event = getEvent(request.args["sref"][0], request.args["idev"][0])
        event['event']['recording_margin_before'] = margin_before
        event['event']['recording_margin_after'] = margin_after
        event['at'] = False
        event['transcoding'] = getTranscodingSupport()
        event['kinopoisk'] = getLanguage()
        return event

    def P_boxinfo(self, request):
        """
        Gather information about current device.

        .. deprecated:: 0.26

            Box image files mainly increase disk space used by package.
            Dubious benefit and unclear licensing/distribution permissions.
            In best case scenario all but one image file is never used.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            dict: key/value pairs
        """
        return getInfo(self.session, need_fullinfo=True)

    def P_epgpop(self, request):
        events = []
        timers = []

        if "sref" in request.args.keys():
            ev = getChannelEpg(request.args["sref"][0])
            events = ev["events"]
        elif "sstr" in request.args.keys():
            fulldesc = False
            if "full" in request.args.keys():
                fulldesc = True
            bouquetsonly = False
            if "bouquetsonly" in request.args.keys():
                bouquetsonly = True
            ev = getSearchEpg(
                request.args["sstr"][0],
                None,
                fulldesc,
                bouquetsonly)
            events = sorted(ev["events"], key=lambda ev: ev['begin_timestamp'])

        if len(events) > 0:
            t = getTimers(self.session)
            timers = t["timers"]

        return {
            "theme": THEMES[0],
            "events": events,
            "timers": timers,
            "at": False,
            "kinopoisk": getLanguage()
        }

    def P_epgdialog(self, request):
        return self.P_epgpop(request)

    def P_screenshot(self, request):
        box = {'brand': "dmm"}

        if getMachineBrand() == 'Vu+':
            box['brand'] = "vuplus"
        elif getMachineBrand() == 'GigaBlue':
            box['brand'] = "gigablue"
        elif getMachineBrand() == 'Edision':
            box['brand'] = "edision"
        elif getMachineBrand() == 'iQon':
            box['brand'] = "iqon"
        elif getMachineBrand() == 'Technomate':
            box['brand'] = "techomate"
        elif os.path.isfile("/proc/stb/info/azmodel"):
            box['brand'] = "azbox"

        return {"box": box}

    def P_powerstate(self, request):
        return {}

    def P_message(self, request):
        return {}

    def P_movies(self, request):
        movies = getMovieList(request.args)
        movies['transcoding'] = getTranscodingSupport()

        sorttype = comp_config.OpenWebif.webcache.moviesort.value
        unsort = movies['movies']

        if sorttype == 'name':
            movies['movies'] = sorted(unsort, key=lambda k: k['eventname'])
        elif sorttype == 'named':
            movies['movies'] = sorted(
                unsort, key=lambda k: k['eventname'], reverse=True)
        elif sorttype == 'date':
            movies['movies'] = sorted(unsort, key=lambda k: k['recordingtime'])
        elif sorttype == 'dated':
            movies['movies'] = sorted(
                unsort, key=lambda k: k['recordingtime'], reverse=True)

        movies['sort'] = sorttype
        return movies

    def P_radio(self, request):
        return {}

    def P_timers(self, request):
        return getTimers(self.session)

    def P_edittimer(self, request):
        return {}

    def P_tv(self, request):
        return {}

    def P_tvradio(self, request):
        epgmode = "tv"
        if "epgmode" in request.args.keys():
            epgmode = request.args["epgmode"][0]
            if epgmode not in ["tv", "radio"]:
                epgmode = "tv"
        return {"epgmode": epgmode}

    def P_config(self, request):
        """
        Request handler for the `config` endpoint.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        section = "usage"
        if "section" in request.args.keys():
            section = request.args["section"][0]
        return getConfigs(section)

    def P_collapsemenu(self, request):
        """
        Request handler for the `collapsemenu` endpoint.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        res = self.testMandatoryArguments(request, ["name"])
        if res:
            return res
        return addCollapsedMenu(request.args["name"][0])

    def P_expandmenu(self, request):
        """
        Request handler for the `expandmenu` endpoint.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        res = self.testMandatoryArguments(request, ["name"])
        if res:
            return res
        return removeCollapsedMenu(request.args["name"][0])

    def P_settings(self, request):
        return {
            "result": True,
            'configsections': getConfigsSections()['sections'],
            'themes': THEMES,
            'theme': THEMES[0],
            'zapstream': getZapStream()['zapstream'],
            'showchannelpicon': getShowChPicon()['showchannelpicon']
        }

    def P_multiepg(self, request):
        epgmode = "tv"
        if "epgmode" in request.args.keys():
            epgmode = request.args["epgmode"][0]
            if epgmode not in ["tv", "radio"]:
                epgmode = "tv"

        bouq = getBouquets(epgmode)
        if "bref" not in request.args.keys():
            bref = bouq['bouquets'][0][0]
        else:
            bref = request.args["bref"][0]
        endtime = 1440
        begintime = -1
        day = 0
        week = 0
        wadd = 0
        if "week" in request.args.keys():
            try:
                week = int(request.args["week"][0])
                wadd = week * 7
            except ValueError:
                pass
        if "day" in request.args.keys():
            try:
                day = int(request.args["day"][0])
                if day > 0 or wadd > 0:
                    now = localtime()
                    begintime = mktime(
                        (now.tm_year, now.tm_mon, now.tm_mday + day + wadd,
                         0, 0, 0, -1, -1, -1))
            except ValueError:
                pass
        mode = 1
        if comp_config.OpenWebif.webcache.mepgmode.value:
            try:
                mode = int(comp_config.OpenWebif.webcache.mepgmode.value)
            except ValueError:
                pass
        epg = getMultiEpg(self, bref, begintime, endtime, mode)
        epg['bouquets'] = bouq['bouquets']
        epg['bref'] = bref
        epg['day'] = day
        epg['week'] = week
        epg['mode'] = mode
        epg['epgmode'] = epgmode
        return epg

    def P_statusinfo(self, request):
        """
        Request handler for the `/statusinfo` endpoint.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        return getStatusInfo(self)

    def P_setmoviesort(self, request):
        """
        Request handler for the `setmoviesort` endpoint.

        .. deprecated:: 0.46

            To be dropped.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        if "nsort" in request.args.keys():
            nsort = request.args["nsort"][0]
            comp_config.OpenWebif.webcache.moviesort.value = nsort
            comp_config.OpenWebif.webcache.moviesort.save()
        return {}

    def P_settheme(self, request):
        """
        Request handler for the `settheme` endpoint.

        .. note::

            Not available in *Enigma2 WebInterface API*.

        .. deprecated:: 0.46

            To be dropped.

        Args:
            request (twisted.web.server.Request): HTTP request object
        Returns:
            HTTP response with headers
        """
        return {}

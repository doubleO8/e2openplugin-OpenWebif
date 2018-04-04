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
import re
import unicodedata
import logging
from time import time, localtime, strftime
from urllib import quote, unquote

from ..i18n import _, tstrings
from ..defaults import PICON_EXT, PICON_PATH
from Components.Sources.ServiceList import ServiceList
from Components.ParentalControl import parentalControl
from Components.config import config
from Components.NimManager import nimmanager
from ServiceReference import ServiceReference
from Screens.ChannelSelection import service_types_tv, service_types_radio, \
    FLAG_SERVICE_NEW_FOUND
from enigma import eServiceCenter, eServiceReference, \
    iServiceInformation, eEPGCache
from info import GetWithAlternative
from info import FALLBACK_PICON_LOCATION, PICON_ENDPOINT_PATH

from model_utilities import mangle_epg_text
from events import FLAGS_WEB, ServicesEventDict

SLOG = logging.getLogger("services")


def getServiceInfoString(info, what):
    v = info.getInfo(what)
    if v == -1:
        return "N/A"
    if v == -2:
        return info.getInfoString(what)
    return v


def getCurrentService(session):
    try:
        info = session.nav.getCurrentService().info()
        return {
            "result": True,
            "name": mangle_epg_text(info.getName()),
            "namespace": getServiceInfoString(info,
                                              iServiceInformation.sNamespace),
            "aspect": getServiceInfoString(info, iServiceInformation.sAspect),
            "provider": getServiceInfoString(info,
                                             iServiceInformation.sProvider),
            "width": getServiceInfoString(info,
                                          iServiceInformation.sVideoWidth),
            "height": getServiceInfoString(info,
                                           iServiceInformation.sVideoHeight),
            "apid": getServiceInfoString(info, iServiceInformation.sAudioPID),
            "vpid": getServiceInfoString(info, iServiceInformation.sVideoPID),
            "pcrpid": getServiceInfoString(info, iServiceInformation.sPCRPID),
            "pmtpid": getServiceInfoString(info, iServiceInformation.sPMTPID),
            "txtpid": getServiceInfoString(info, iServiceInformation.sTXTPID),
            "tsid": getServiceInfoString(info, iServiceInformation.sTSID),
            "onid": getServiceInfoString(info, iServiceInformation.sONID),
            "sid": getServiceInfoString(info, iServiceInformation.sSID),
            "ref": quote(
                getServiceInfoString(info, iServiceInformation.sServiceref),
                safe=' ~@#$&()*!+=:;,.?/\''),
            "iswidescreen": info.getInfo(iServiceInformation.sAspect) in (
                3, 4, 7, 8, 0xB, 0xC, 0xF, 0x10)
        }
    except Exception:
        return {
            "result": False,
            "name": "",
            "namespace": "",
            "aspect": 0,
            "provider": "",
            "width": 0,
            "height": 0,
            "apid": 0,
            "vpid": 0,
            "pcrpid": 0,
            "pmtpid": 0,
            "txtpid": "N/A",
            "tsid": 0,
            "onid": 0,
            "sid": 0,
            "ref": "",
            "iswidescreen": False
        }


def getBouquets(stype):
    s_type = service_types_tv
    s_type2 = "bouquets.tv"
    if stype == "radio":
        s_type = service_types_radio
        s_type2 = "bouquets.radio"
    serviceHandler = eServiceCenter.getInstance()
    services = serviceHandler.list(
        eServiceReference(
            '%s FROM BOUQUET "%s" ORDER BY bouquet' %
            (s_type, s_type2)))
    bouquets = services and services.getContent("SN", True)
    bouquets = removeHiddenBouquets(bouquets)
    return {"bouquets": bouquets}


def removeHiddenBouquets(bouquetList):
    bouquets = bouquetList
    if hasattr(eServiceReference, 'isInvisible'):
        for bouquet in bouquetList:
            flags = int(bouquet[0].split(':')[1])
            if flags & eServiceReference.isInvisible and bouquet in bouquets:
                bouquets.remove(bouquet)
    return bouquets


def getSatellites(stype):
    ret = []
    s_type = service_types_tv
    if stype == "radio":
        s_type = service_types_radio
    refstr = '%s FROM SATELLITES ORDER BY satellitePosition' % (s_type)
    ref = eServiceReference(refstr)
    serviceHandler = eServiceCenter.getInstance()
    servicelist = serviceHandler.list(ref)
    if servicelist is not None:
        while True:
            service = servicelist.getNext()
            if not service.valid():
                break
            unsigned_orbpos = service.getUnsignedData(4) >> 16
            orbpos = service.getData(4) >> 16
            if orbpos < 0:
                orbpos += 3600
            if service.getPath().find("FROM PROVIDER") != -1:
                # service_type = _("Providers")
                continue
            elif service.getPath().find(
                            "flags == %d" % (FLAG_SERVICE_NEW_FOUND)) != -1:
                service_type = _("New")
            else:
                service_type = _("Services")
            try:
                service_name = str(nimmanager.getSatDescription(orbpos))
            except BaseException:
                if unsigned_orbpos == 0xFFFF:  # Cable
                    service_name = _("Cable")
                elif unsigned_orbpos == 0xEEEE:  # Terrestrial
                    service_name = _("Terrestrial")
                else:
                    if orbpos > 1800:  # west
                        orbpos = 3600 - orbpos
                        h = _("W")
                    else:
                        h = _("E")
                    service_name = ("%d.%d" + h) % (orbpos / 10, orbpos % 10)
            service.setName("%s - %s" % (service_name, service_type))
            ret.append({
                "service": service.toString(),
                "name": service.getName()
            })
    ret = sortSatellites(ret)
    return {"satellites": ret}


def sortSatellites(satList):
    sortDict = {}
    i = 0
    for k in satList:
        result = re.search(
            "[(]\s*satellitePosition\s*==\s*(\d+)\s*[)]",
            k["service"],
            re.IGNORECASE)
        if result is None:
            return satList
        orb = int(result.group(1))
        if orb > 3600:
            orb *= -1
        elif orb > 1800:
            orb -= 3600
        if orb not in sortDict:
            sortDict[orb] = []
        sortDict[orb].append(i)
        i += 1
    outList = []
    for l in sorted(sortDict.keys()):
        for v in sortDict[l]:
            outList.append(satList[v])
    return outList


def getServices(sRef, showAll=True, showHidden=False, pos=0):
    services = []

    if sRef == "":
        sRef = '%s FROM BOUQUET "bouquets.tv" ORDER BY bouquet' % (
            service_types_tv)

    servicelist = ServiceList(eServiceReference(sRef))
    slist = servicelist.getServicesAsList()

    for sitem in slist:
        st = int(sitem[0].split(":")[1])
        if (sitem[0][:7] == '1:832:D') or (not (st & 512) and not (st & 64)):
            pos = pos + 1
        if not st & 512 or showHidden:
            if showAll or st == 0:
                service = {}
                service['pos'] = 0 if (st & 64) else pos
                service['servicereference'] = unicode(
                    sitem[0], 'utf_8', errors='ignore').encode(
                    'utf_8', 'ignore')
                service['program'] = int(
                    service['servicereference'].split(':')[3], 16)
                service['servicename'] = unicode(
                    sitem[1], 'utf_8', errors='ignore').encode(
                    'utf_8', 'ignore')
                services.append(service)

    return {"services": services, "pos": pos}


def getAllServices(type):
    services = []
    if type is None:
        type = "tv"
    bouquets = getBouquets(type)["bouquets"]
    pos = 0
    for bouquet in bouquets:
        sv = getServices(bouquet[0], True, False, pos)
        services.append({
            "servicereference": bouquet[0],
            "servicename": bouquet[1],
            "subservices": sv["services"]
        })
        pos = sv["pos"]

    return {
        "result": True,
        "services": services
    }


def getPlayableServices(sRef, sRefPlaying):
    if sRef == "":
        sRef = '%s FROM BOUQUET "bouquets.tv" ORDER BY bouquet' % (
            service_types_tv)

    services = []
    servicecenter = eServiceCenter.getInstance()
    servicelist = servicecenter.list(eServiceReference(sRef))
    servicelist2 = servicelist and servicelist.getContent('S') or []

    for service in servicelist2:
        # 512 is hidden service on sifteam image. Doesn't affect other images
        if not int(service.split(":")[1]) & 512:
            service2 = {}
            service2['servicereference'] = service
            info = servicecenter.info(eServiceReference(service))
            service2['isplayable'] = info.isPlayable(
                eServiceReference(service), eServiceReference(sRefPlaying)) > 0
            services.append(service2)

    return {
        "result": True,
        "services": services
    }


def getPlayableService(sRef, sRefPlaying):
    servicecenter = eServiceCenter.getInstance()
    info = servicecenter.info(eServiceReference(sRef))
    return {
        "result": True,
        "service": {
            "servicereference": sRef,
            "isplayable": info.isPlayable(
                eServiceReference(sRef),
                eServiceReference(sRefPlaying)) > 0}}


def getSubServices(session):
    # TODO: duplicated .. stream/getStreamSubservices
    services = []
    service = session.nav.getCurrentService()
    if service is not None:
        services.append({"servicereference": service.info().getInfoString(
            iServiceInformation.sServiceref),
            "servicename": service.info().getName()})
        subservices = service.subServices()
        if subservices and subservices.getNumberOfSubservices() > 0:
            SLOG.debug(
                "subservices.getNumberOfSubservices() yielded {!r}".format(
                    subservices.getNumberOfSubservices()))
            for i in range(subservices.getNumberOfSubservices()):
                sub = subservices.getSubservice(i)
                services.append({
                    "servicereference": sub.toString(),
                    "servicename": sub.getName()
                })
    else:
        services.append({
            "servicereference": "N/A",
            "servicename": "N/A"
        })

    return {"services": services}


def getEvent(ref, idev):
    epgcache = eEPGCache.getInstance()
    events = epgcache.lookupEvent(['IBDTSENRX', (ref, 2, int(idev))])
    info = {}
    for event in events:
        info['id'] = event[0]
        info['begin_str'] = strftime("%H:%M", (localtime(event[1])))
        info['begin'] = event[1]
        info['end'] = strftime("%H:%M", (localtime(event[1] + event[2])))
        info['duration'] = event[2]
        info['title'] = mangle_epg_text(event[3])
        info['shortdesc'] = event[4]
        info['longdesc'] = event[5]
        info['channel'] = mangle_epg_text(event[6])
        info['sref'] = event[7]
        break
    return {'event': info}


def getChannelEpg(ref, begintime=-1, endtime=-1):
    ret = []
    ev = {}
    use_empty_ev = False
    if ref:
        ref = unquote(ref)

        # When quering EPG we dont need URL, also getPicon doesn't like URL
        if "://" in ref:
            ref = ":".join(ref.split(":")[:10]) + "::" + ref.split(":")[-1]

        picon = getPicon(ref)
        epgcache = eEPGCache.getInstance()
        events = epgcache.lookupEvent(
            ['IBDTSENC', (ref, 0, begintime, endtime)])
        if events is not None:
            for event in events:
                ev = {}
                ev['picon'] = picon
                ev['id'] = event[0]
                if event[1]:
                    ev['date'] = "%s %s" % (tstrings[(
                        "day_" + strftime("%w", (localtime(event[1]))))],
                                            strftime("%d.%m.%Y",
                                                     (localtime(event[1]))))
                    ev['begin'] = strftime("%H:%M", (localtime(event[1])))
                    ev['begin_timestamp'] = event[1]
                    ev['duration'] = int(event[2] / 60)
                    ev['duration_sec'] = event[2]
                    ev['end'] = strftime(
                        "%H:%M", (localtime(event[1] + event[2])))
                    ev['title'] = mangle_epg_text(event[3])
                    ev['shortdesc'] = event[4]
                    ev['longdesc'] = event[5]
                    ev['sref'] = ref
                    ev['sname'] = mangle_epg_text(event[6])
                    ev['tleft'] = int(((event[1] + event[2]) - event[7]) / 60)
                    if ev['duration_sec'] == 0:
                        ev['progress'] = 0
                    else:
                        ev['progress'] = int(
                            ((event[7] - event[1]) * 100 / event[2]) * 4)
                    ev['now_timestamp'] = event[7]
                    ret.append(ev)
                else:
                    use_empty_ev = True
                    ev['sref'] = ref
    else:
        use_empty_ev = True
        ev['sref'] = ""

    if use_empty_ev:
        ev['date'] = 0
        ev['begin'] = 0
        ev['begin_timestamp'] = 0
        ev['duration'] = 0
        ev['duration_sec'] = 0
        ev['end'] = 0
        ev['title'] = "N/A"
        ev['shortdesc'] = ""
        ev['sname'] = ""
        ev['longdesc'] = ""
        ev['tleft'] = 0
        ev['progress'] = 0
        ev['now_timestamp'] = 0
        ret.append(ev)

    return {"events": ret, "result": True}


def getBouquetEpg(ref, begintime=-1, endtime=None, mangle_html=True):
    ret = []
    services = eServiceCenter.getInstance().list(eServiceReference(ref))
    if not services:
        return {"events": ret, "result": False}

    search = [FLAGS_WEB]
    for service in services.getContent('S'):
        if endtime:
            search.append((service, 0, begintime, endtime))
        else:
            search.append((service, 0, begintime))

    epgcache = eEPGCache.getInstance()
    events = epgcache.lookupEvent(search)
    if not events:
        return {"events": [], "result": True}

    for raw_data in events:
        ret.append(ServicesEventDict(
            raw_data, now_next_mode=False, mangle_html=mangle_html))

    return {"events": ret, "result": True}


def getServicesNowNextEpg(sList, mangle_html=True):
    ret = []
    if not sList:
        return {"events": ret, "result": False}

    sRefList = sList.split(",")
    search = [FLAGS_WEB]
    for service in sRefList:
        search.append((service, 0, -1))
        search.append((service, 1, -1))

    epgcache = eEPGCache.getInstance()
    events = epgcache.lookupEvent(search)
    if not events:
        return {"events": [], "result": True}

    for raw_data in events:
        ret.append(ServicesEventDict(
            raw_data, now_next_mode=True, mangle_html=mangle_html))

    return {"events": ret, "result": True}


def getBouquetNowNextEpg(ref, servicetype, mangle_html=True):
    ret = []
    services = eServiceCenter.getInstance().list(eServiceReference(ref))
    if not services:
        return {"events": ret, "result": False}

    search = [FLAGS_WEB]
    if servicetype == -1:
        for service in services.getContent('S'):
            search.append((service, 0, -1))
            search.append((service, 1, -1))
    else:
        for service in services.getContent('S'):
            search.append((service, servicetype, -1))

    epgcache = eEPGCache.getInstance()
    events = epgcache.lookupEvent(search)

    if not events:
        return {"events": [], "result": True}

    for raw_data in events:
        e_data = ServicesEventDict(
            raw_data, now_next_mode=False, mangle_html=mangle_html)
        if e_data['sref'] is not None:
            achannels = GetWithAlternative(e_data['sref'], False)
            if achannels:
                e_data['asrefs'] = achannels
        ret.append(e_data)

    return {"events": ret, "result": True}


def getNowNextEpg(ref, servicetype, mangle_html=True):
    ret = []
    epgcache = eEPGCache.getInstance()
    events = epgcache.lookupEvent([FLAGS_WEB, (ref, servicetype, -1)])

    if not events:
        return {"events": [], "result": True}

    for raw_data in events:
        ret.append(ServicesEventDict(
            raw_data, now_next_mode=True, mangle_html=mangle_html))

    return {"events": ret, "result": True}


def getSearchEpg(sstr, endtime=None, fulldesc=False, bouquetsonly=False):
    """
    Search for EPG events.

    Args:
        sstr (basestring): search term
        endtime (int): timetamp
        fulldesc (bool): search in event's description field too
        bouquetsonly (bool): limit results to services in known bouquets

    Returns:
        list: event datasets
    """
    bsref = {}
    events = []
    epgcache = eEPGCache.getInstance()
    search_type = eEPGCache.PARTIAL_TITLE_SEARCH

    if config.OpenWebif.epg_encoding.value != 'utf-8':
        try:
            sstr = sstr.encode(config.OpenWebif.epg_encoding.value)
        except UnicodeEncodeError:
            pass

    if fulldesc:
        if hasattr(eEPGCache, 'FULL_DESCRIPTION_SEARCH'):
            search_type = eEPGCache.FULL_DESCRIPTION_SEARCH
    results = epgcache.search(('IBDTSENR', 128, search_type, sstr, 1))

    if results:
        if bouquetsonly:
            # collect service references from TV bouquets
            for service in getAllServices('tv')['services']:
                for service2 in service['subservices']:
                    bsref[service2['servicereference']] = True
                else:
                    bsref[service['servicereference']] = True

        for event in results:
            if bouquetsonly and not event[7] in bsref:
                continue
            day_val = strftime("%w", (localtime(event[1])))
            date_val = strftime("%d.%m.%Y", (localtime(event[1])))
            ev = dict()
            ev['id'] = event[0]
            ev['date'] = "%s %s" % (tstrings[("day_" + day_val)], date_val)
            ev['begin_timestamp'] = event[1]
            ev['begin'] = strftime("%H:%M", (localtime(event[1])))
            ev['duration_sec'] = event[2]
            ev['duration'] = int(event[2] / 60)
            ev['end'] = strftime("%H:%M", (localtime(event[1] + event[2])))
            ev['title'] = mangle_epg_text(event[3])
            ev['shortdesc'] = event[4]
            ev['longdesc'] = event[5]
            ev['sref'] = event[7]
            ev['sname'] = mangle_epg_text(event[6])
            ev['picon'] = getPicon(event[7])
            ev['now_timestamp'] = None
            if endtime:
                # don't show events if begin is after endtime
                if event[1] <= endtime:
                    events.append(ev)
            else:
                events.append(ev)

    return {"events": events, "result": True}


def getSearchSimilarEpg(ref, eventid):
    ref = unquote(ref)
    ret = []
    epgcache = eEPGCache.getInstance()
    events = epgcache.search(
        ('IBDTSENR', 128, eEPGCache.SIMILAR_BROADCASTINGS_SEARCH,
         ref, eventid))

    if events is not None:
        for event in events:
            day_val = strftime("%w", (localtime(event[1])))
            date_val = strftime("%d.%m.%Y", (localtime(event[1])))
            ev = {}
            ev['id'] = event[0]
            ev['date'] = "%s %s" % (tstrings[("day_" + day_val)], date_val)
            ev['begin_timestamp'] = event[1]
            ev['begin'] = strftime("%H:%M", (localtime(event[1])))
            ev['duration_sec'] = event[2]
            ev['duration'] = int(event[2] / 60)
            ev['end'] = strftime("%H:%M", (localtime(event[1] + event[2])))
            ev['title'] = event[3]
            ev['shortdesc'] = event[4]
            ev['longdesc'] = event[5]
            ev['sref'] = event[7]
            ev['sname'] = mangle_epg_text(event[6])
            ev['picon'] = getPicon(event[7])
            ev['now_timestamp'] = None
            ret.append(ev)

    return {"events": ret, "result": True}


def getPicon(sname):
    if not PICON_PATH:
        return FALLBACK_PICON_LOCATION

    # remove URL part
    if ("://" in sname) or ("%3a//" in sname) or ("%3A//" in sname):
        sname = unquote(sname)
        sname = ":".join(sname.split(":")[:10]) + "::" + sname.split(":")[-1]

    sname = GetWithAlternative(sname)
    if sname is not None:
        pos = sname.rfind(':')
    else:
        return FALLBACK_PICON_LOCATION

    cname = None
    if pos != -1:
        cname = ServiceReference(sname[:pos].rstrip(':')).getServiceName()
        sname = sname[:pos].rstrip(':').replace(':', '_') + PICON_EXT
    filename = PICON_PATH + sname

    if os.path.isfile(filename):
        return PICON_ENDPOINT_PATH + sname

    fields = sname.split('_', 8)
    if len(fields) > 7 and not fields[6].endswith("0000"):
        # remove "sub-network" from namespace
        fields[6] = fields[6][:-4] + "0000"
        sname = '_'.join(fields)
        filename = PICON_PATH + sname
        if os.path.isfile(filename):
            return PICON_ENDPOINT_PATH + sname

    if len(fields) > 1 and fields[0] != '1':
        # fallback to 1 for other reftypes
        fields[0] = '1'
        sname = '_'.join(fields)
        filename = PICON_PATH + sname
        if os.path.isfile(filename):
            return PICON_ENDPOINT_PATH + sname

    if len(fields) > 3 and fields[2] != '1':
        # fallback to 1 for tv services with nonstandard servicetypes
        fields[2] = '1'
        sname = '_'.join(fields)
        filename = PICON_PATH + sname
        if os.path.isfile(filename):
            return PICON_ENDPOINT_PATH + sname

    if cname is not None:  # picon by channel name
        cname1 = mangle_epg_text(cname).replace(
            '/', '_').encode('utf-8', 'ignore')

        if os.path.isfile(PICON_PATH + cname1 + PICON_EXT):
            return PICON_ENDPOINT_PATH + cname1 + PICON_EXT

        cname = unicodedata.normalize(
            'NFKD', unicode(cname, 'utf_8', errors='ignore')).encode(
            'ASCII', 'ignore')
        cname = re.sub(
            '[^a-z0-9]',
            '',
            cname.replace('&', 'and').replace(
                '+', 'plus').replace(
                '*', 'star').lower())

        if len(cname) > 0:
            filename = PICON_PATH + cname + PICON_EXT

        if os.path.isfile(filename):
            return PICON_ENDPOINT_PATH + cname + PICON_EXT

        if len(cname) > 2 and cname.endswith(
                'hd') and os.path.isfile(PICON_PATH + cname[:-2] + PICON_EXT):
            return PICON_ENDPOINT_PATH + cname[:-2] + PICON_EXT


def getParentalControlList():
    if config.ParentalControl.configured.value:
        return {
            "result": True,
            "services": []
        }
    parentalControl.open()
    if config.ParentalControl.type.value == "whitelist":
        tservices = parentalControl.whitelist
    else:
        tservices = parentalControl.blacklist
    services = []
    if tservices is not None:
        for service in tservices:
            tservice = ServiceReference(service)
            services.append({
                "servicereference": service,
                "servicename": tservice.getServiceName()
            })
    return {
        "result": True,
        "type": config.ParentalControl.type.value,
        "services": services
    }

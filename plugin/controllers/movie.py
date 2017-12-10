#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import enigma
from enigma import eServiceReference, iServiceInformation

from models.events import mangle_event

SERVICE_INFORMATION_FIELDS = [
    'sAspect',
    'sAudioPID',
    'sCAIDPIDs',
    'sCAIDs',
    'sCurrentChapter',
    'sCurrentTitle',
    'sDVBState',
    'sDescription',
    'sFileSize',
    'sFrameRate',
    'sHBBTVUrl',
    'sIsCrypted',
    'sIsIPStream',
    'sIsMultichannel',
    'sIsScrambled',
    'sLiveStreamDemuxId',
    'sNamespace',
    'sONID',
    'sPCRPID',
    'sPMTPID',
    'sProgressive',
    'sProvider',
    'sSID',
    'sServiceref',
    'sTSID',
    'sTXTPID',
    'sTagAlbum',
    'sTagAlbumGain',
    'sTagAlbumPeak',
    'sTagAlbumSortname',
    'sTagAlbumVolumeCount',
    'sTagAlbumVolumeNumber',
    'sTagArtist',
    'sTagArtistSortname',
    'sTagAttachment',
    'sTagAudioCodec',
    'sTagBeatsPerMinute',
    'sTagBitrate',
    'sTagCRC',
    'sTagChannelMode',
    'sTagCodec',
    'sTagComment',
    'sTagComposer',
    'sTagContact',
    'sTagCopyright',
    'sTagCopyrightURI',
    'sTagDate',
    'sTagDescription',
    'sTagEncoder',
    'sTagEncoderVersion',
    'sTagExtendedComment',
    'sTagGenre',
    'sTagHomepage',
    'sTagISRC',
    'sTagImage',
    'sTagKeywords',
    'sTagLanguageCode',
    'sTagLicense',
    'sTagLicenseURI',
    'sTagLocation',
    'sTagMaximumBitrate',
    'sTagMinimumBitrate',
    'sTagNominalBitrate',
    'sTagOrganization',
    'sTagPerformer',
    'sTagPreviewImage',
    'sTagReferenceLevel',
    'sTagSerial',
    'sTagTitle',
    'sTagTitleSortname',
    'sTagTrackCount',
    'sTagTrackGain',
    'sTagTrackNumber',
    'sTagTrackPeak',
    'sTagVersion',
    'sTagVideoCodec',
    'sTags',
    'sTimeCreate',
    'sTotalChapters',
    'sTotalTitles',
    'sTransferBPS',
    'sTransponderData',
    'sUser',
    'sVideoHeight',
    'sVideoPID',
    'sVideoType',
    'sVideoWidth',
]

SERVICE_REFERENCE_ID = {
    eServiceReference.idDVB: "DVB",
    eServiceReference.idFile: "File",
    eServiceReference.idInvalid: "Invalid",
    eServiceReference.idServiceMP3: "ServiceMP3",
    eServiceReference.idStructure: "Structure",
    eServiceReference.idUser: "User",
}

SERVICE_REFERENCE_FLAG = {
    eServiceReference.isDirectory: "Directory",
    eServiceReference.isGroup: "Group",
    eServiceReference.isMarker: "Marker",
    eServiceReference.isNumberedMarker: "NumberedMarker",

    eServiceReference.canDescent: "canDescent",
    eServiceReference.mustDescent: "mustDescent",
    eServiceReference.shouldSort: "shouldSort",
    eServiceReference.hasSortKey: "hasSortKey",
}


def flags_description(flags):
    global SERVICE_REFERENCE_FLAG

    flag_list = []
    for flag in SERVICE_REFERENCE_FLAG:
        if flags & flag:
            flag_list.append(SERVICE_REFERENCE_FLAG[flag])

    return flag_list


def mangle_servicereference(servicereference):
    global SERVICE_REFERENCE_ID
    data = dict()

    if isinstance(servicereference, basestring):
        servicereference = eServiceReference(servicereference)

    data['kind'] = SERVICE_REFERENCE_ID.get(servicereference.type,
                                            "INVALID")
    data['path'] = servicereference.getPath().decode("utf-8")
    data['servicereference'] = servicereference.toString().decode("utf-8")
    data['flags'] = servicereference.flags
    return data


class MoviesController(object):
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.service_center_instance = enigma.eServiceCenter.getInstance()
        self.events_with_component_data = kwargs.get("component_data", False)

    def mangle_servicereference_information(self, servicereference):
        data = dict()
        meta = dict()

        cs_info = self.service_center_instance.info(servicereference)

        for fkey in SERVICE_INFORMATION_FIELDS:
            try:
                const_value = getattr(iServiceInformation, fkey)
                current_value = cs_info.getInfo(servicereference, const_value)
                if current_value == -2:
                    current_value = cs_info.getInfoString(
                        servicereference, const_value).decode("utf-8")
                elif current_value == -3:
                    current_value = cs_info.getInfoObject(servicereference,
                                                          const_value)
                if current_value == -1:
                    continue
                key = fkey[1:]
                meta[key] = current_value
                if key == 'FileSize':
                    meta[key] = current_value & 0xffffffff
            except Exception as exc:
                self.log.error(exc)

        data['meta'] = meta
        event = cs_info.getEvent(servicereference)
        if event:
            data['event'] = mangle_event(
                event, with_component_data=self.events_with_component_data)

        return data

    def list_movies(self, root_path):
        self.log.debug('%s',
                       "Trying to list files in {!r}".format(root_path))
        root_servicereference = eServiceReference(
            eServiceReference.idFile, 0, root_path)

        list_result = self.service_center_instance.list(root_servicereference)
        items = list_result.getContent("NR", True)
        for (shortinfo, serviceref) in items:
            item = mangle_servicereference(serviceref)
            item['label'] = shortinfo.decode("utf-8")
            if item['flags'] & eServiceReference.isDirectory:
                for sub_item in self.list_movies(serviceref.getPath()):
                    yield sub_item
            else:
                item.update(
                    self.mangle_servicereference_information(serviceref))
                yield item

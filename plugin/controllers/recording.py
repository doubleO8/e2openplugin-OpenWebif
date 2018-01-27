#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os

import enigma
from enigma import eServiceReference, iServiceInformation

from models.events import mangle_event, KEY_SERVICE_REFERENCE
from models.model_utilities import mangle_epg_text
from utilities import parse_cuts

#: root path where recordings are stored
RECORDINGS_ROOT_PATH = '/media/hdd/movie/'

#: Endpoint path portion: list of recordings
RECORDINGS_ENDPOINT_PATH = 'recordings'

#: Endpoint path portion: recording
RECORDING_ENDPOINT_PATH = 'recording'

#: Endpoint URL: recording
RECORDING_ENDPOINT_URL = ''.join(('/', RECORDING_ENDPOINT_PATH, '/'))

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


def mangle_servicereference(servicereference, encoding=None):
    global SERVICE_REFERENCE_ID
    if encoding is None:
        encoding = "utf-8"
    data = dict()

    if isinstance(servicereference, basestring):
        servicereference = eServiceReference(servicereference)

    data['kind'] = SERVICE_REFERENCE_ID.get(servicereference.type, "INVALID")
    data['path'] = servicereference.getPath().decode(encoding)
    data[KEY_SERVICE_REFERENCE] = servicereference.toString()
    data['flags'] = servicereference.flags
    return data


class RecordingsController(object):
    def __init__(self, *args, **kwargs):
        self.log = logging.getLogger(__name__)
        self.service_center_instance = enigma.eServiceCenter.getInstance()
        self.events_with_component_data = kwargs.get("component_data", False)
        self.encoding = kwargs.get("encoding", "utf-8")
        self.service_lookup = dict()

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
                        servicereference, const_value).decode(self.encoding)
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

        try:
            recording_s = meta['Serviceref']
            data['recording_servicename'] = self.service_lookup[recording_s]
        except KeyError:
            data['recording_servicename'] = self.get_servicename(
                servicereference)

        return data

    def get_servicename(self, servicereference, encoding=None):
        if encoding is None:
            encoding = "utf-8"

        if isinstance(servicereference, basestring):
            servicereference = eServiceReference(servicereference)

        actual_servicereference = self.service_center_instance.info(
            servicereference).getInfoString(
            servicereference, iServiceInformation.sServiceref)
        es = eServiceReference(actual_servicereference)
        value = self.service_center_instance.info(es).getName(es).decode(
            encoding)
        value = mangle_epg_text(value)
        # self.log.info("{!r} -> {!r}".format(actual_servicereference, value))
        self.service_lookup[actual_servicereference] = value
        return value

    def list_movies(self, root_path):
        self.log.debug('%s', "Trying to list files in {!r}".format(root_path))
        root_servicereference = eServiceReference(
            eServiceReference.idFile, 0, root_path)

        list_result = self.service_center_instance.list(root_servicereference)
        items = list_result.getContent("NR", True)
        for (shortinfo, serviceref) in items:
            item = mangle_servicereference(serviceref, encoding=self.encoding)
            item['label'] = shortinfo.decode(self.encoding)
            if item['flags'] & eServiceReference.isDirectory:
                for sub_item in self.list_movies(serviceref.getPath()):
                    yield sub_item
            else:
                item.update(
                    self.mangle_servicereference_information(serviceref))

                cutfile = (item['path'] + '.cuts').encode('utf-8')
                if os.path.isfile(cutfile):
                    try:
                        item['meta']['marks'] = parse_cuts(cutfile)
                    except Exception as exc:
                        self.log.error(exc)

                yield item

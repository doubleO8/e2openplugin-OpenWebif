import pprint

import enigma
from enigma import eServiceReference, iServiceInformation

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


def mangle_event(event_obj):
    data = dict(
        start_time=event_obj.getBeginTime(),
        duration=event_obj.getBeginTime(),
        title=event_obj.getEventName().decode("utf-8"),
        shortinfo=event_obj.getShortDescription().decode("utf-8"),
        longinfo=event_obj.getExtendedDescription().decode("utf-8"),
        item_id=event_obj.getEventId(),
    )
    data['component_data'] = event_obj.getComponentData()
    return data

def mangle_servicereference_information(servicereference):
    global SERVICE_INFORMATION_FIELDS
    global iServiceInformation
    global ech
    global mangle_event
    data = dict()
    meta = dict()

    cs_info = ech.info(servicereference)

    # print("Service Info Dump:")
    for fkey in SERVICE_INFORMATION_FIELDS:
        try:
            const_value = getattr(iServiceInformation, fkey)
            current_value = cs_info.getInfo(servicereference, const_value)
            if current_value == -2:
                current_value = cs_info.getInfoString(servicereference, const_value).decode("utf-8")
            elif current_value == -3:
                current_value = cs_info.getInfoObject(servicereference, const_value)
            if current_value == -1:
                continue
            key = fkey[1:]
            # print("{:3d} {!s:40}: {!r}".format(const_value, key, current_value))
            meta[key] = current_value
            if key == 'FileSize':
                meta[key] = current_value & 0xffffffff
        except Exception as exc:
            print(repr(exc))

    data['meta'] = meta
    event = cs_info.getEvent(servicereference)
    if event:
        data['event'] = mangle_event(event)

    return data


def flags_description(flags):
    global SERVICE_REFERENCE_FLAG

    flag_list = []
    for flag in SERVICE_REFERENCE_FLAG:
        if flags & flag:
            flag_list.append(SERVICE_REFERENCE_FLAG[flag])

    return flag_list

def mangle_servicereference(servicereference):
    global SERVICE_REFERENCE_ID
    global eServiceReference
    data = dict()

    if isinstance(servicereference, basestring):
        servicereference = eServiceReference(servicereference)

    data['kind'] = SERVICE_REFERENCE_ID.get(servicereference.type, "INVALID")
    data['path'] = servicereference.getPath().decode("utf-8")
    data['servicereference'] = servicereference.toString().decode("utf-8")
    data['flags'] = servicereference.flags
    return data


root_path = '/media/hdd/movie/'
ech = enigma.eServiceCenter.getInstance()


def list_movies(root_path):
    global ech
    global mangle_servicereference
    global mangle_servicereference_information
    global list_movies
    global flags_description

    root_servicereference = eServiceReference(
        eServiceReference.idFile, 0, root_path)

    list_result = ech.list(root_servicereference)
    items = list_result.getContent("NR", True)
    for (shortinfo, serviceref) in items:
        item = mangle_servicereference(serviceref)
        if item['flags'] & eServiceReference.isDirectory:
            for sub_item in list_movies(serviceref.getPath()):
                yield sub_item
        else:
            item.update(mangle_servicereference_information(serviceref))
            yield item

for item in list_movies(root_path):
    print("{!r}".format(item['path']))
    pprint.pprint(item)

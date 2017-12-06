import enigma
import pprint
#pprint.pprint(dir(enigma.iServiceInformation))
from enigma import iServiceInformation

fields = [
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

cs = self.session.nav.getCurrentService()
cs_info = cs.info()

for fkey in fields:
    try:
        const_value = getattr(iServiceInformation, fkey)
        current_value = cs_info.getInfo(const_value)
        if current_value == -2:
            current_value = cs_info.getInfoString(const_value).decode("utf-8")
        elif current_value == -3:
            current_value = cs_info.getInfoObject(const_value)
        if current_value == -1:
            continue
        print("{:3d} {!s:40}: {!r}".format(const_value, fkey[1:], current_value))
    except Exception as exc:
        print(repr(exc))

event_obj = cs_info.getEvent(cs_info.getInfo(iServiceInformation.sServiceref))
#print dir(event_obj)
event_keys = [
    'getBeginTime', 'getBeginTimeString', 'getComponentData', 'getDuration', 
    'getEPGSource', 'getEventId', 'getEventName', 'getExtendedDescription', 
    'getExtraEventData', 'getLinkageService', 'getNumOfLinkageServices', 
#    'getPtrString', 
    'getShortDescription'
]

for evk in event_keys:
    try:
        func = getattr(event_obj, evk)
        current_value = func()
    except Exception as exc:
        print(repr(exc))
        current_value = None
    print("{!s}: {!r}".format(evk, current_value))

fi = cs.frontendInfo()
fi_keys = [
    'getAll', 'getFrontendData', 'getFrontendInfo', 'getFrontendStatus', 
#    'getTransponderData'
]

for fi_key in fi_keys:
    try:
        func = getattr(fi, fi_key)
        current_value = func()
    except Exception as exc:
        print fi_key
        print(repr(exc))
        current_value = None
    print("{!s}: {!r}".format(fi_key, current_value))

#print dir(fi)
#print fi.__dict__
print("getAll:")
pprint.pprint(fi.getAll(True))
print("getTransponderData:")
pprint.pprint(fi.getTransponderData(True))
#print cs_info.getName()
#print repr(cs_info.getEvent(cs_info.getInfo(iServiceInformation.sServiceref)))
#print dir(cs_info)

import enigma
import pprint

from enigma import eServiceReference, iServiceInformation
from Screens.ChannelSelection import service_types_tv, service_types_radio
import Screens
from Components.MovieList import MovieList
#print dir(Screens.ChannelSelection)

ech = enigma.eServiceCenter.getInstance()

if 1 == 2:
    #                                   v-- enigma2 is very sensitive here ...
    items = ech.list(eServiceReference('%s ORDER BY name' % service_types_tv))
    # S=serviceref, N=name
    for item in items.getContent("SN", True):
        pprint.pprint(item)


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

def dump_service_info(cs_info, serviceref):
    global SERVICE_INFORMATION_FIELDS
    global iServiceInformation
#>>> -1814257664 & 0xffffffff
#2480709632
#>>>  2139578556 & 0xffffffff
#2139578556

    print("Service Info Dump:")
    for fkey in SERVICE_INFORMATION_FIELDS:
        #print fkey, getattr(iServiceInformation, fkey), cs_info
        try:
            const_value = getattr(iServiceInformation, fkey)
            current_value = cs_info.getInfo(serviceref, const_value)
            if current_value == -2:
                current_value = cs_info.getInfoString(serviceref, const_value).decode("utf-8")
            elif current_value == -3:
                current_value = cs_info.getInfoObject(serviceref, const_value)
            if current_value == -1:
                continue
            print("{:3d} {!s:40}: {!r}".format(const_value, fkey[1:], current_value))
        except Exception as exc:
            print(repr(exc))

def dump_servicereference(some_ref):
    global SERVICE_REFERENCE_ID
    global SERVICE_REFERENCE_FLAG
    global eServiceReference

    if isinstance(some_ref, basestring):
        some_ref = eServiceReference(some_ref)

    print("Service Reference Dump:")
    bli = [
        # 4         , 2            , 8           , 16
        #'canDescent', 'mustDescent', 'shouldSort', 'hasSortKey',
        # flags value:
        #'flags', 

        # 7
        #'flagDirectory', 

        #'getData',  # ??
        'getName', 'getPath', 'getSortKey', 
        #'getUnsignedData',  # ??

        # type IDs:
        #'idDVB', 'idFile', 'idInvalid', 'idServiceMP3', 'idStructure', 'idUser', 

        # flags (?):
        # 1          , 128      , 64        , 256
        #'isDirectory', 'isGroup', 'isMarker', 'isNumberedMarker', 
        
        # setter (?):
        #'setData', 'setName', 'setPath', 'setUnsignedData', 
        'sort1', 
        'toCompareString', 
        #'toString', 
        #'type', 
        #'valid',
    ]

    print("-" * 80)
    print some_ref.toString()
    print("id kind {!r}".format(SERVICE_REFERENCE_ID.get(some_ref.type, "INVALID")))
    flag_list = []
    for flag in SERVICE_REFERENCE_FLAG:
        if some_ref.flags & flag:
            flag_list.append(SERVICE_REFERENCE_FLAG[flag])
    print("flags   {:08b} {!s}".format(some_ref.flags, '|'.join(flag_list)))

    for evk in bli:
        label = evk
        try:
            func = getattr(some_ref, evk)
            if callable(func):
                label += " [C]"
                current_value = func()
            else:
                current_value = func
        except Exception as exc:
            print("{!r}: {!r}".format(evk, exc))
            current_value = None
        print("{!s:20}: {!r}".format(label, current_value))
    print("=" * 80)
    print("")

event_keys = [
    'getBeginTime', 'getBeginTimeString', 'getComponentData', 'getDuration', 
    'getEPGSource', 'getEventId', 'getEventName', 'getExtendedDescription', 
    'getExtraEventData', 'getLinkageService', 'getNumOfLinkageServices', 
#    'getPtrString', 
    'getShortDescription'
]

def dump_event(event_obj):
    global event_keys
    print("Event Dump:")
    print dir(event_obj)
    for evk in event_keys:
        try:
            func = getattr(event_obj, evk)
            current_value = func()
        except Exception as exc:
            print(repr(exc))
            current_value = None
        print("{!s}: {!r}".format(evk, current_value))

some_ref2 = eServiceReference(4097, 0, "haha")
print some_ref2.toString(), some_ref2.valid()
print eServiceReference("/etc/passwd").toString()
print eServiceReference('2:0:1:0:0:0:0:0:0:0:/etc/passwd').toString()
print eServiceReference('2:0:1:0:0:0:0:22:0:0:/etc/passwd').toString()
some_ref = eServiceReference('0:/etc/passwd')
print some_ref.toString()
print some_ref.valid()

dump_servicereference(some_ref2)
dump_servicereference('0:/etc/passwd')
dump_servicereference(eServiceReference(4097, 17, "haha"))
dump_servicereference(eServiceReference(4097, eServiceReference.isDirectory|eServiceReference.isMarker, "haha"))
dump_servicereference(eServiceReference('2:0:1:0:0:0:0:0:0:0:/etc/passwd'))


MOVIE_LIST_SREF_ROOT = '2:0:0:0:0:0:0:0:0:0:'
root = eServiceReference(MOVIE_LIST_SREF_ROOT + '/media/hdd/movie/')
root = eServiceReference(eServiceReference.idFile, 0, '/media/hdd/movie/')
if 2 == 3:
    #                     v-- servicereference or None
    movielist = MovieList(root)
    #movielist.load(root, None)

    mlist = movielist.list
mlist = ech.list(root)
print dir(mlist)
#pprint.pprint(mlist.getNext())
items = mlist.getContent("CNRS", True)
for (cee, shortinfo, serviceref, see) in items[:10]:
    #pprint.pprint((cee, shortinfo, serviceref, see))
    info = ech.info(serviceref)
    dump_servicereference(serviceref)
    if info is not None:
        dump_service_info(info, serviceref)
        event = info.getEvent(serviceref)
        if not event:
            continue
        dump_event(event)
    print("~" * 80)

print len(items)

if 1 == 3:
    for (serviceref, info, begin, unknown) in mlist:
        # pprint.pprint((serviceref, info, begin, unknown))
        dump_servicereference(serviceref)
        if info is not None:
            dump_service_info(info, serviceref)
            event = info.getEvent(serviceref)
            if not event:
                continue
            dump_event(event)

    print len(mlist)

if 4 == 5:
    dump_servicereference(eServiceReference(1, 17, "haha"))


if 22 == 22:
    print dir(eServiceReference)
    print("service_types_tv={!r}".format(service_types_tv))
    print("service_types_radio={!r}".format(service_types_radio))
    #service_types_tv = '1:7:1:0:0:0:0:0:0:0:(type == 1) || ' \
    #                   '(type == 17) || (type == 22) || (type == 25) || ' \
    #                   '(type == 31) || (type == 134) || (type == 195)'
    #service_types_radio = '1:7:2:0:0:0:0:0:0:0:(type == 2) || (type == 10)'


some110 = eServiceReference("1:0:1:412:4:85:FFFF0000:0:0:0:")
print "x-" * 80
print ""
sinfo = ech.info(some110)
print sinfo.getName(some110)
print some110.toString()
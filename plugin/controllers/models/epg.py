#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    B begin
    C current time
    I id
    D duration
    T title
    S shortinfo
    E longinfo
    R service_reference
    N service_name
"""
# The fields fetched by filterName() and convertDesc() all need to be
# html-escaped, so do it there.
#
from model_utilities import mangle_epg_text
from cgi import escape as html_escape


def filterName(name):
    if name is not None:
        name = html_escape(mangle_epg_text(name), quote=True)
    return name


def convertDesc(val):
    if val is not None:
        return html_escape(
            unicode(val, 'utf_8', errors='ignore').encode('utf_8', 'ignore'),
            quote=True)
    return val


FLAG_BEGIN = "B"
FLAG_CURRENT_TIME = "C"
FLAG_LONGINFO = "E"
FLAG_DURATION = "D"
FLAG_ITEM_ID = "I"
FLAG_SERVICE_NAME = "N"
FLAG_SERVICE_REFERENCE = "R"
FLAG_SHORTINFO = "S"
FLAG_TITLE = "T"

FLAGS_FULL = ''.join(sorted(
    [FLAG_BEGIN, FLAG_CURRENT_TIME, FLAG_LONGINFO, FLAG_DURATION, FLAG_ITEM_ID,
     FLAG_SERVICE_NAME, FLAG_SERVICE_REFERENCE, FLAG_SHORTINFO, FLAG_TITLE]))

FLAGS_ALL = ''.join(sorted(
    [FLAG_BEGIN, FLAG_LONGINFO, FLAG_DURATION, FLAG_ITEM_ID,
     FLAG_SERVICE_NAME, FLAG_SERVICE_REFERENCE, FLAG_SHORTINFO, FLAG_TITLE]))

FLAGS_WEB = 'IBDCTSERN'

SERVICES_KEY_MAP = {
    'id': FLAGS_WEB.index(FLAG_ITEM_ID),
    'begin_timestamp': FLAGS_WEB.index(FLAG_BEGIN),
    'duration_sec': FLAGS_WEB.index(FLAG_DURATION),
    'title': FLAGS_WEB.index(FLAG_TITLE),
    'shortdesc': FLAGS_WEB.index(FLAG_SHORTINFO),
    'longdesc': FLAGS_WEB.index(FLAG_LONGINFO),
    'sref': FLAGS_WEB.index(FLAG_SERVICE_REFERENCE),
    'sname': FLAGS_WEB.index(FLAG_SERVICE_NAME),
    'now_timestamp': FLAGS_WEB.index(FLAG_CURRENT_TIME),
}


class ServicesEventDict(dict):
    """
    """

    def __init__(self, raw_data, now_next_mode=False, mangle_html=True):
        """
        >>> dd_in = (123, 1506020400, 120*60, 1506020440, "DASDING Sprechstunde", None, None, "1:0:2:6F37:431:A401:FFFF0000:0:0:0:", "DASDING")
        >>> sed = ServicesEventDict(dd_in)
        >>> sed['id']
        123
        >>> sed['begin_timestamp']
        1506020400
        >>> sed['duration_sec']
        7200
        """
        dict.__init__(self)
        for key in SERVICES_KEY_MAP:
            idx = SERVICES_KEY_MAP[key]
            self[key] = raw_data[idx]

        if mangle_html:
            for key in ('shortdesc', 'longdesc', 'sname'):
                if key in ('shortdesc', 'longdesc'):
                    self[key] = convertDesc(self[key])
                elif key == 'sname':
                    self[key] = filterName(self[key])

        if now_next_mode:
            if self['begin_timestamp'] == 0:
                self['duration_sec'] = 0
                self['title'] = 'N/A'
                self['shortdesc'] = ''
                self['longdesc'] = ''
                self['now_timestamp'] = 0
                self['remaining'] = 0
            else:
                current_timestamp = self['now_timestamp']
                if current_timestamp > self['begin_timestamp']:
                    self['remaining'] = self['begin_timestamp'] + self[
                        'duration_sec'] - current_timestamp
                else:
                    self['remaining'] = self['duration_sec']


if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))

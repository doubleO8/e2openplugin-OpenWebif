#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. seealso::

    :ref:`event_format-label`
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

#: Begin
FLAG_BEGIN = "B"
#: Current Time
FLAG_CURRENT_TIME = "C"
#: Long Event Information
FLAG_LONGINFO = "E"
#: Duration
FLAG_DURATION = "D"
#: ID
FLAG_ITEM_ID = "I"
#: Service Name
FLAG_SERVICE_NAME = "N"
#: Short Service Name
FLAG_SHORT_SERVICE_NAME = "n"
#: Service Reference
FLAG_SERVICE_REFERENCE = "R"
#: Short Event Information
FLAG_SHORTINFO = "S"
#: Event Title
FLAG_TITLE = "T"

#: Event Flags including Current Time Field
FLAGS_FULL = ''.join(sorted(
    [FLAG_BEGIN, FLAG_CURRENT_TIME, FLAG_LONGINFO, FLAG_DURATION, FLAG_ITEM_ID,
     FLAG_SERVICE_NAME, FLAG_SERVICE_REFERENCE, FLAG_SHORTINFO, FLAG_TITLE]))

#: Event Flags without Current Time Field
FLAGS_ALL = ''.join(sorted(
    [FLAG_BEGIN, FLAG_LONGINFO, FLAG_DURATION, FLAG_ITEM_ID,
     FLAG_SERVICE_NAME, FLAG_SERVICE_REFERENCE, FLAG_SHORTINFO, FLAG_TITLE]))

#: Event Flags as used in :py:class:`controllers.web`
FLAGS_WEB = 'IBDCTSERN'

#: Services Key Map
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

#: Event Field Map
EVENT_FIELD_MAP = {
    "B": "begin",
    "C": "current_time",
    "I": "id",
    "D": "duration",
    "T": "title",
    "S": "shortinfo",
    "E": "longinfo",
    "R": "service_reference",
    "N": "service_name",
    "n": "shortservice_name",
}


class EventDict(dict):
    """
    Event data container object

    >>> dd_in = (123, 1506020400, 120*60, 1506020440, "DASDING Sprechstunde", None, None, "1:0:2:6F37:431:A401:FFFF0000:0:0:0:", "DASDING")
    >>> sed = EventDict(dd_in)
    >>> sed['id']
    123
    >>> sed['begin']
    1506020400
    >>> sed['duration']
    7200
    """
    def __init__(self, raw_data, flag_string=None):
        dict.__init__(self)
        if flag_string is None:
            flag_string = FLAGS_WEB
        flags = list(flag_string.replace("X", ''))
        for flag_key, value in zip(flags, raw_data):
            key = EVENT_FIELD_MAP[flag_key]
            self[key] = value
        self._mangle()

    def _mangle(self):
        text_keys = ("shortinfo", "longinfo", "title",
                     "service_name", "shortservice_name")
        for tkey in text_keys:
            if tkey in self:
                self[tkey] = mangle_epg_text(self[tkey])


class ServicesEventDict(dict):
    """
    Event data container object as used by EPG lookups in services.py

    .. deprecated:: 0.31 replaced by :obj:`EventDict`

    >>> dd_in = (123, 1506020400, 120*60, 1506020440, "DASDING Sprechstunde", None, None, "1:0:2:6F37:431:A401:FFFF0000:0:0:0:", "DASDING")
    >>> sed = ServicesEventDict(dd_in)
    >>> sed['id']
    123
    >>> sed['begin_timestamp']
    1506020400
    >>> sed['duration_sec']
    7200
    """
    def __init__(self, raw_data, now_next_mode=False, mangle_html=True):
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
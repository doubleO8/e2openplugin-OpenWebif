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

if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))

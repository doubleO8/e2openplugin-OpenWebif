#!/usr/bin/env python
# -*- coding: utf-8 -*-

def mangle_epg_text(value):
    return value.replace(
        '\xc2\x86', '').replace('\xc2\x87', '').replace('\xc2\x8a', '\n')


if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))

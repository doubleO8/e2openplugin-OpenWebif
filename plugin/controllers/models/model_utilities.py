#!/usr/bin/env python
# -*- coding: utf-8 -*-


def mangle_epg_text(value):
    """
    Remove EPG data-specific utf-8 characters.
    Replace EPG specific newline character 0xc28a with `newline`.

    Args:
        request (:obj:`basestring`): EPG text
    Returns:
        (:obj:`basestring`): mangled EPG text
    """
    if value is None:
        return value
    return value.replace(
        '\xc2\x86', '').replace('\xc2\x87', '').replace('\xc2\x8a', '\n')


if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))

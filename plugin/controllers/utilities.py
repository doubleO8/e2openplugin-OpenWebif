#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re
import urllib
import urlparse
import struct
import time
import datetime
from wsgiref.handlers import format_date_time
import unicodedata

CONTRIB = os.path.join(os.path.dirname(__file__), '../../contrib')

MANY_SLASHES_PATTERN = r'[\/]+'
MANY_SLASHES_REGEX = re.compile(MANY_SLASHES_PATTERN)

PATTERN_ITEM_OR_KEY_ACCESS = r'^(?P<attr_name>[a-zA-Z][\w\d]*)' \
                             r'\[((?P<index>\d+)|' \
                             r'[\'\"](?P<key>[\s\w\d]+)[\'\"])\]$'
REGEX_ITEM_OR_KEY_ACCESS = re.compile(PATTERN_ITEM_OR_KEY_ACCESS)

SERVICEREFERENCE_PORTION_PATTERN = r'([\da-fA-F]+)[^\w]?'
SERVICEREFERENCE_PORTION_REGEX = re.compile(SERVICEREFERENCE_PORTION_PATTERN)

#: regular expression pattern for strings containing something resembling
#: a hostname/port combination (``<hostname>:<port>``)
PATTERN_HOST_HEADER = r'(\[(?P<ipv6_addr>.+?)\]|(?P<hostname>.+?))' \
                      r'(\:(?P<port>\d+))?$'
REGEX_HOST_HEADER = re.compile(PATTERN_HOST_HEADER)

# stolen from enigma2_http_api ...
# https://wiki.neutrino-hd.de/wiki/Enigma:Services:Formatbeschreibung
# Dezimalwert: 1=TV, 2=Radio, 4=NVod, andere=Daten

SERVICE_TYPE_TV = 0x01
SERVICE_TYPE_RADIO = 0x02
SERVICE_TYPE_SD4 = 0x10
SERVICE_TYPE_HDTV = 0x19
SERVICE_TYPE_UHD = 0x1f
SERVICE_TYPE_OPT = 0xd3

SERVICE_KIND_COMMENT = 0x64

# type 1 = digital television service
# type 2 = digital radio sound service
# type 4 = nvod reference service (NYI)
# type 10 = advanced codec digital radio sound service
# type 17 = MPEG-2 HD digital television service
# type 22 = advanced codec SD digital television
# type 24 = advanced codec SD NVOD reference service (NYI)
# type 25 = advanced codec HD digital television
# type 27 = advanced codec HD NVOD reference service (NYI)


SERVICE_TYPE = {
    'TV': SERVICE_TYPE_TV,
    'HDTV': SERVICE_TYPE_HDTV,
    'RADIO': SERVICE_TYPE_RADIO,
    'UHD': SERVICE_TYPE_UHD,
    'SD4': SERVICE_TYPE_SD4,
    'OPT': SERVICE_TYPE_OPT,
}

SERVICE_TYPE_LOOKUP = {v: k for k, v in SERVICE_TYPE.iteritems()}

#: Namespace - DVB-C services
NS_DVB_C = 0xffff0000

#: Namespace - DVB-S services
NS_DVB_S = 0x00c00000

#: Namespace - DVB-T services
NS_DVB_T = 0xeeee0000

#: Label:Namespace map
NS = {
    'DVB-C': NS_DVB_C,
    'DVB-S': NS_DVB_S,
    'DVB-T': NS_DVB_T,
}

#: Namespace:Label lookup map
NS_LOOKUP = {v: k for k, v in NS.iteritems()}

CUTS_IN = 0
CUTS_OUT = 1
CUTS_MARK = 2
CUTS_WATCHMARK = 3


def lenient_decode(value, encoding=None):
    """
    Decode an encoded string and convert it to an unicode string.

    Args:
            value: input value
            encoding: string encoding, defaults to utf-8
    Returns:
            :obj:`unicode`: decoded value

    >>> lenient_decode("Hallo")
    u'Hallo'
    >>> lenient_decode(u"Hallo")
    u'Hallo'
    >>> lenient_decode("HällöÜ")
    u'H\\xe4ll\\xf6\\xdc'
    """
    if isinstance(value, unicode):
        return value

    if encoding is None:
        encoding = 'utf_8'

    return value.decode(encoding, 'ignore')


def lenient_force_utf_8(value):
    """

    Args:
            value: input value
    Returns:
            :obj:`basestring` utf-8 encoded value

    >>> isinstance(lenient_force_utf_8(''), basestring)
    True
    >>> lenient_force_utf_8(u"Hallo")
    'Hallo'
    >>> lenient_force_utf_8("HällöÜ")
    'H\\xc3\\xa4ll\\xc3\\xb6\\xc3\\x9c'
    """
    return lenient_decode(value).encode('utf_8')


def sanitise_filename_slashes(value):
    """

    Args:
            value(basestring): input value
    Returns:
            value w/o multiple slashes

    >>> in_value = "///tmp/x/y/z"
    >>> expected = re.sub("^/+", "/", "///tmp/x/y/z")
    >>> sanitise_filename_slashes(in_value) == expected
    True
    """
    return re.sub(MANY_SLASHES_REGEX, '/', value)


def get_config_attribute(path, root_obj, head=None):
    """
    Determine attribute of *root_obj* to be accessed by *path* in a
    (somewhat) safe manner.
    This implementation will allow key and index based accessing too
    (e.g. ``config.some_list[0]`` or ``config.some_dict['some_key']``)
    The *path* value needs to start with *head* (default='config').

    Args:
        path: character string specifying which attribute is to be accessed
        root_obj: An object whose attributes are to be accessed.
        head: Value of the first portion of *path*

    Returns:
        Attribute of *root_obj*

    Raises:
        ValueError: If *path* is invalid.
        AttributeError: If attribute cannot be accessed
    """
    if head is None:
        head = 'config'
    portions = path.split('.')

    if len(portions) < 2:
        raise ValueError('Invalid path length')

    if portions[0] != head:
        raise ValueError(
            'Head is {!r}, expected {!r}'.format(portions[0], head))

    current_obj = root_obj

    for attr_name in portions[1:]:
        if not attr_name:
            raise ValueError("empty attr_name")

        if attr_name.startswith('_'):
            raise ValueError('private member')

        matcher = REGEX_ITEM_OR_KEY_ACCESS.match(attr_name)

        if matcher:
            gdict = matcher.groupdict()
            attr_name = gdict.get('attr_name')
            next_obj = getattr(current_obj, attr_name)

            if gdict.get("index"):
                index = int(gdict.get("index"))
                current_obj = next_obj[index]
            else:
                key = gdict["key"]
                current_obj = next_obj[key]
        else:
            current_obj = getattr(current_obj, attr_name)

    return current_obj


def parse_servicereference(serviceref, separators=None, extended=False):
    """
    Parse a Enigma2 style service reference string representation.

    Args:
        serviceref: Enigma2 style service reference
        separators: Allowed separators

    Returns:
        dict containing parsed values

    Raises:
        ValueError: If *serviceref* is invalid.

    >>> sref = '1:0:1:300:7:85:00c00000:0:0:0:'
    >>> result = parse_servicereference(sref)
    >>> result
    {'service_type': 1, 'oid': 133, 'tsid': 7, 'ns': 12582912, 'sid': 768}
    >>> sref_dashes = '1-0-1-300-7-85-00c00000-0-0-0-'
    >>> result_dashes = parse_servicereference(sref_dashes, ':-')
    >>> result == result_dashes
    True
    >>> sref_g = create_servicereference(**result)
    >>> sref_g
    '1:0:1:300:7:85:00c00000:0:0:0:'
    >>> sref_g2 = create_servicereference(result)
    >>> sref_g2
    '1:0:1:300:7:85:00c00000:0:0:0:'
    >>> sref == sref_g
    True
    >>> sref2 = '1:64:A:0:0:0:0:0:0:0::SKY Sport'
    >>> result2 = parse_servicereference(sref2)
    >>> result2
    {'service_type': 10, 'oid': 0, 'tsid': 0, 'ns': 0, 'sid': 0}
    >>> result2e = parse_servicereference(sref2, extended=True)
    >>> result2e['kind']
    100
    >>> sref3 = '1:0:0:0:0:0:0:0:0:0:/media/hdd/movie/20170921 2055 - DASDING - DASDING Sprechstunde - .ts'  # NOQA
    >>> result3 = parse_servicereference(sref3)
    >>> result3
    {'service_type': 0, 'oid': 0, 'tsid': 0, 'ns': 0, 'sid': 0}
    """
    if separators is None:
        separators = (':',)
    elif isinstance(separators, basestring):
        separators = list(separators)

    for separator in separators:
        parts = serviceref.split(separator)
        try:
            sref_data = {
                'service_type': int(parts[2], 16),
                'sid': int(parts[3], 16),
                'tsid': int(parts[4], 16),
                'oid': int(parts[5], 16),
                'ns': int(parts[6], 16)
            }
            if extended:
                sref_data['kind'] = int(parts[1], 16)
            return sref_data
        except IndexError:
            continue

    raise ValueError(separators)


def create_servicereference(*args, **kwargs):
    """
    Generate a (Enigma2 style) service reference string representation.

    :param args[0]: Service Reference Parameter as dict
    :type args[0]: :class:`dict`

    :param service_type: Service Type
    :type service_type: int

    :param sid: SID
    :type sid: int

    :param tsid: TSID
    :type tsid: int

    :param oid: OID
    :type oid: int

    :param ns: Enigma2 Namespace
    :type ns: int
    """
    if len(args) == 1 and isinstance(args[0], dict):
        kwargs = args[0]
    service_type = kwargs.get('service_type', 0)
    sid = kwargs.get('sid', 0)
    tsid = kwargs.get('tsid', 0)
    oid = kwargs.get('oid', 0)
    ns = kwargs.get('ns', 0)

    return '{:x}:0:{:x}:{:x}:{:x}:{:x}:{:08x}:0:0:0:'.format(
        1,
        service_type,
        sid,
        tsid,
        oid,
        ns)


def get_servicereference_portions(value, raise_on_empty=False):
    """
    Try to match possible portions of a servicereference in *value*.

    Args:
        value (basestring): a servicereference-like string
        raise_on_empty (boolean): If a ValueError should be raised

    Returns:
        list: matched portions

    Raises:
        ValueError: If result is empty list and *raise_on_empty* is True

    >>> deadbeef = ['de', 'ad', 'be', 'ef']
    >>> get_servicereference_portions(None)
    []
    >>> get_servicereference_portions(True)
    []
    >>> get_servicereference_portions(False)
    []
    >>> get_servicereference_portions('de:ad:be:ef') == deadbeef
    True
    >>> get_servicereference_portions('de,ad$be_ef??') == deadbeef
    True
    >>> get_servicereference_portions('-1:ad:be:ef:')
    ['1', 'ad', 'be', 'ef']
    >>> get_servicereference_portions('-^ghi', raise_on_empty=True)
    Traceback (most recent call last):
        ...
    ValueError: -^ghi
    >>> get_servicereference_portions('1:0:19:7C:6:85:FFFF0000:0:0:0:')
    ['1', '0', '19', '7C', '6', '85', 'FFFF0000', '0', '0', '0']
    """
    rv = []
    try:
        rv = re.findall(SERVICEREFERENCE_PORTION_REGEX, value)
    except TypeError:
        pass

    if not rv and raise_on_empty:
        raise ValueError(value)

    return rv


def mangle_snp(value):
    """
    Mangle service_name as suggested by SNP (Service Name Picons)

    .. seealso::

        * https://github.com/picons/picons-source
        * https://github.com/OpenViX/enigma2/blob/master/lib/python/Components/Renderer/Picon.py#L88-L89

    Args:
        value (basestring): service name

    Returns:
        str: normalised service name

    >>> mangle_snp('?ANTENNE? BAYERN')
    'antennebayern'
    >>> mangle_snp('?Sky? ?Cine?ma +?24?')
    'skycinemaplus24'
    """
    unicode_value = lenient_decode(value, 'utf_8')
    name = unicodedata.normalize('NFKD', unicode_value).encode(
        'ASCII', 'ignore')
    normalised = name.replace(
        '&', 'and').replace('+', 'plus').replace('*', 'star').lower()
    return re.sub('[^a-z0-9]', '', normalised)


def require_valid_file_parameter(request, parameter_key):
    """

    Args:
        request (twisted.web.server.Request): HTTP request object
        parameter_key: filename parameter key

    Returns:
        basestring: existing filename

    Raises:
        ValueError: If *parameter_key* is missing.
        IOError: If filename does not point to an existing file path
    """
    if parameter_key not in request.args:
        raise ValueError("Missing parameter: {!r}".format(parameter_key))

    filename = lenient_force_utf_8(
        urllib.unquote_plus(request.args[parameter_key][0]))
    filename = sanitise_filename_slashes(os.path.realpath(filename))

    if not os.path.exists(filename):
        raise IOError("Not a file: {!r}".format(filename))

    return filename


def build_url(hostname, path=None, args=None, scheme="http", port=None):
    """
    Create an URL based on parameters.

    Args:
        hostname: hostname portion
        path: path portion
        args: query parameters
        scheme: scheme portion
        port: port portion

    Returns:
        basestring: Generated URL

    >>> build_url("some.host", "/", {})
    'http://some.host/'
    >>> build_url("some.host", "/")
    'http://some.host/'
    >>> build_url("some.host")
    'http://some.host'
    >>> build_url("some.host", port=27080)
    'http://some.host:27080'
    >>> build_url("", port=27080)
    Traceback (most recent call last):
        ...
    ValueError: empty hostname!
    >>> build_url("some.host", "x")
    'http://some.host/x'
    >>> build_url("some.host", "/x")
    'http://some.host/x'
    >>> build_url("some.host", "/x/")
    'http://some.host/x/'
    >>> build_url("some.host", "x/")
    'http://some.host/x/'
    >>> build_url("some.host", "x/../")
    'http://some.host/x/../'
    >>> build_url("some.host", "/:x/äöü-blabla/")
    'http://some.host/%3Ax/%C3%A4%C3%B6%C3%BC-blabla/'
    >>> build_url("some.host", u'/:x/\xe4\xf6\xfc-blabla/'.encode('utf-8'))
    'http://some.host/%3Ax/%C3%A4%C3%B6%C3%BC-blabla/'
    """
    if not hostname:
        raise ValueError("empty hostname!")

    netloc = hostname
    if port:
        netloc = '{:s}:{!s}'.format(hostname, port)
    if path:
        path_q = urllib.quote(path)
    else:
        path_q = ''
    if args:
        args_e = urllib.urlencode(args)
    else:
        args_e = None
    return urlparse.urlunparse((scheme, netloc, path_q, None, args_e, None))


def mangle_host_header_port(value=None,
                            fallback_port="80", fallback_hostname="localhost",
                            want_url=False):
    """

    Args:
        value: header data
        fallback_port: fallback value for port (default ``80``)
        fallback_hostname: fallback value for hostname (default ``localhost``)
        want_url: return an URL string

    Returns:
        dict: Mangled *port, proto* values

    >>> resi1 = mangle_host_header_port()
    >>> resi1['netloc']
    'localhost'
    >>> resi2 = mangle_host_header_port("localhost:80")
    >>> resi2['netloc']
    'localhost'
    >>> resi3 = mangle_host_header_port("x:123")
    >>> resi3['netloc']
    'x:123'
    >>> resi4 = mangle_host_header_port("haha:342111")
    >>> resi4['netloc']
    'haha'
    >>> resi5 = mangle_host_header_port("haha:342111", want_url=True)
    >>> resi5
    'http://haha'
    >>> resi6 = mangle_host_header_port("localhost:12345", want_url=True)
    >>> resi6
    'http://localhost:12345'
    >>> mangle_host_header_port("[2001:0db8:85a3:08d3::0370:7344]", want_url=True)  # NOQA
    'http://[2001:0db8:85a3:08d3::0370:7344]'
    >>> mangle_host_header_port("[2001:0db8:85a3:08d3::0370:7344]")['netloc']
    '[2001:0db8:85a3:08d3::0370:7344]'
    >>> mangle_host_header_port("[2001:0db8:85a3:08d3::0370:7344]:8080/", want_url=True)  # NOQA
    'http://[2001:0db8:85a3:08d3::0370:7344]:8080/'
    >>> mangle_host_header_port("[2001:0db8:85a3:08d3::0370:7344]:8080")['netloc']  # NOQA
    '[2001:0db8:85a3:08d3::0370:7344]:8080'
    """
    result = dict(
        proto="http",  # deprecated, added just for compatibility
        scheme="http",
        port=fallback_port,
        hostname=fallback_hostname
    )

    if value:
        matcher = re.match(REGEX_HOST_HEADER, value)
        if matcher:
            gdict = matcher.groupdict()
            result["port"] = gdict["port"]
            if gdict.get("ipv6_addr"):
                result["hostname"] = '[{ipv6_addr}]'.format(**gdict)
            else:
                result["hostname"] = gdict["hostname"]

    try:
        port_i = int(result['port'])
        if not 1 <= port_i <= 65535:
            raise ValueError(result['port'])
    except Exception:
        result['port'] = fallback_port

    if result['port'] not in ("80", 80):
        result['netloc'] = "{hostname}:{port}".format(**result)
    else:
        result['netloc'] = result["hostname"]

    if want_url:
        if result['port'] in ("80", 80):
            port = None
        else:
            port = result['port']

        return build_url(hostname=result['hostname'],
                         scheme=result['scheme'],
                         port=port)
    return result


def parse_cuts(cutfile):
    marks = {
        "watched": 0,
        "maximum": 0,
        "marks": []
    }

    with open(cutfile, "rb") as source:
        chunk = source.read(12)

        while chunk:
            (pts_value, cue_kind) = struct.unpack('>QI', chunk)
            seconds = pts_value / 90000
            if cue_kind == CUTS_WATCHMARK:
                marks['watched'] = seconds
            else:
                marks['marks'].append([seconds, cue_kind])

            chunk = source.read(12)

        if marks['marks']:
            marks['maximum'] = marks['marks'][-1][0]

    return marks


def add_expires_header(request, expires=False):
    """

    Args:
        request (twisted.web.server.Request): HTTP request object
        expires: expiration in seconds or False for *imediately / no caching*
    """
    headers = {}
    if expires is False:
        headers[
            'Cache-Control'] = 'no-store, no-cache, must-revalidate, ' \
                               'post-check=0, pre-check=0, max-age=0'
        headers['Expires'] = '-1'
    else:
        now = datetime.datetime.now()
        expires_time = now + datetime.timedelta(seconds=expires)
        headers['Cache-Control'] = 'public'
        headers['Expires'] = format_date_time(
            time.mktime(expires_time.timetuple()))

    for key in headers:
        # self.log.debug(
        #     "CACHE: {key}={val}".format(key=key, val=headers[key]))
        request.setHeader(key, headers[key])


def parse_simple_index(source):
    """

    >>> snp_index = os.path.join(CONTRIB, 'picon-source/snp.index')
    >>> snp = parse_simple_index(snp_index)
    >>> len(snp.keys()) > 1
    True
    >>> snp['wdrduesseldorf']
    'wdr'
    >>> snp['wdrdusseldorf']
    'wdr'
    """
    lookup = dict()

    with open(source, "rb") as src:
        for line in src:
            (key, sep, value) = line.strip().partition('=')
            if key == value:
                continue
            lookup[key] = value

    return lookup


def gen_reverse_proxy_configuration(configuration=None, template=None):
    if template is None:
        template = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                'reverse_proxy.conf.template'))
    if configuration is None:
        configuration = dict()

    with open(template, "rb") as src:
        template_content = src.read()

    fallback_values = {
        "REVERSE_PROXY_PORT": 8000,
        "ENIGMA2_HOST": "localhost",
        "ENIGMA2_PORT": 80,
        "OSCAM_PORT": 83,
        "STREAM_PORT": 8001,
        "STREAM_TRANSCODED_PORT": 8002,
        "PUBLIC_ROOT": '/tmp/public',
        "PICON_ROOT": '/tmp/picon',
    }

    for key in fallback_values:
        value = configuration.get(key, fallback_values[key])
        if key in ('PUBLIC_ROOT', 'PICON_ROOT'):
            value = re.sub(r'\/+$', '', value)
        search_key = '{{{:s}}}'.format(key)
        template_content = template_content.replace(search_key, str(value))
    return template_content

if __name__ == '__main__':
    import doctest

    (FAILED, SUCCEEDED) = doctest.testmod()
    print("[doctest] SUCCEEDED/FAILED: {:d}/{:d}".format(SUCCEEDED, FAILED))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import requests

ENV_VAR = "ENIGMA2_HTTP_API_HOST"

ENV_VAL_FALLBACK = "127.0.0.1"

PAYLOAD_FALLBACK = """
import platform
print platform.system()
"""


def evil_client(base_url, payload=None):
    endpoint = "{base_url}/api/evil".format(base_url=base_url)

    if payload is None:
        payload = PAYLOAD_FALLBACK

    req = requests.post(endpoint, data={"uma": payload})
    print("Request to {!r} yielded HTTP status code {:d}".format(
        endpoint, req.status_code))
    data = req.json()
    if data.get("uma") is True:
        print data['stdout']
    else:
        print data.get("exception")


def dump_disclaimer():
    print("In order for this test to work the environment variable")
    print(">>> {var: ^70} <<<".format(var=ENV_VAR))
    print("needs to be set to the hostname/network location of an "
          "enigma2 device reachable by this script!")
    print("If this is not the case, the fallback value")
    print(">>> {val: ^70} <<<".format(val=ENV_VAL_FALLBACK))
    print("will be used!")
    print("")
    print("We will be using the network location {val!r}:".format(
        val=os.environ.get(ENV_VAR, ENV_VAL_FALLBACK)))
    print("")
    print("")


if __name__ == '__main__':
    dump_disclaimer()
    base_url = "http://{:s}".format(os.environ.get(ENV_VAR, ENV_VAL_FALLBACK))
    payload = None
    for key in ('http_proxy', 'https_proxy'):
        try:
            del os.environ[key]
        except KeyError:
            pass

    if len(sys.argv) > 1:
        source = sys.argv[1]
        print("Payload: {!r}".format(source))
        with open(source, "rb") as src:
            payload = src.read()

    evil_client(base_url, payload)

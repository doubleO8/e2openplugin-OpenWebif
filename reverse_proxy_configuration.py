#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json

from plugin.controllers.utilities import gen_reverse_proxy_configuration

LOCAL_CONFIGURATION = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'revproxy_local_conf.json'))

LOCAL_NGINX_TARGET = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'e2revproxy.conf'))

configuration = None

if os.path.isfile(LOCAL_CONFIGURATION):
    print("Using local configuration values: {!r}".format(LOCAL_CONFIGURATION))
    with open(LOCAL_CONFIGURATION, "rb") as src:
        configuration = json.load(src)

print("Writing nginx configuration file: {!r}".format(LOCAL_NGINX_TARGET))
with open(LOCAL_NGINX_TARGET, "wb") as tgt:
    tgt.write(gen_reverse_proxy_configuration(configuration))

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import hashlib
import pprint
import json

PLUGIN_ROOT = os.path.abspath(os.path.join('..', 'plugin'))

def get_hash(filename):
    hasher = hashlib.sha256()
    with open(filename, "rb") as src:
        hasher.update(src.read())
    return hasher.hexdigest()

if __name__ == '__main__':
    templates_map = {}
    alias_map = {}
    to_delete = list()

    for root, dirs, files in os.walk(PLUGIN_ROOT):
        for filename in files:
            if not filename.endswith('.tmpl'):
                continue
            filename_abs = os.path.join(root, filename)
            checksum = get_hash(filename_abs)
            try:
                templates_map[checksum].append(filename_abs)
            except KeyError:
                templates_map[checksum] = [filename_abs]
    # pprint.pprint(templates_map)

    for key in templates_map:
        raw_items = templates_map[key]
        if len(raw_items) == 1:
            continue

        items = []

        for raw in raw_items:
            (trunk, _) = os.path.splitext(os.path.basename(raw))
            items.append(trunk)

        for filename_abs in raw_items[1:]:
            to_delete.append(filename_abs)

        first = items[0]
        for alias in items[1:]:
            alias_map[alias] = first
    pprint.pprint(alias_map)
    pprint.pprint(to_delete)
    with open("template_aliases.json", "wb") as tgt:
        json.dump(alias_map, tgt, indent=2)
    for item in to_delete:
        os.unlink(item)
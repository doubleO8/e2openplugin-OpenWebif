#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil

from jinja2 import Environment, PackageLoader

from beppo.defaults import PACKAGE_META, OUTPUT_PATH

if __name__ == '__main__':
    env = Environment(loader=PackageLoader('beppo', 'templates'))
    template = env.get_template('opkg_filename')
    current_opk_link = os.path.join(OUTPUT_PATH, 'latest.opk')
    if not os.path.isdir(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)

    if os.path.islink(current_opk_link):
        os.unlink(current_opk_link)

    src_filename = template.render(**PACKAGE_META).strip()
    tgt_filename = os.path.join(OUTPUT_PATH, os.path.basename(src_filename))
    shutil.copy(src_filename, tgt_filename)

    index_template = env.get_template('index.html')
    index_filename = os.path.join(OUTPUT_PATH, "index.html")
    index_content = {
        "files": [
            dict(
                filename=os.path.basename(src_filename),
                description="latest release"),
            dict(
                filename='flake8_report.txt',
                description="flake8 report"),
            dict(
                filename='jshint_report.txt',
                description="JsHint report"),
        ],
        "meta": PACKAGE_META
    }

    with open(index_filename, "wb") as target:
        target.write(index_template.render(**index_content))

    old_cwd = os.getcwd()
    os.chdir(OUTPUT_PATH)
    os.symlink(os.path.basename(src_filename),
               os.path.basename(current_opk_link))
    os.chdir(old_cwd)

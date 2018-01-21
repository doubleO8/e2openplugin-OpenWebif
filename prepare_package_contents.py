#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import glob
import subprocess
import compileall
import json
import datetime

from jinja2 import Environment, PackageLoader

from beppo.defaults import PACKAGE_OUTPUT_PATH, PACKAGE_META, OUTPUT_PATH
from beppo.defaults import TARGET_PATH_REL, TAG_PATH_REL

COMPILE_PO_CALL_FMT = '{binary} -o "{target}" "{source}"'
COMPILE_CHEETAH_CALL_FMT = '{binary} compile -R "{target}"'
JINJA_ENV = Environment(loader=PackageLoader('beppo', 'templates'))


def source_files(top):
    for root, _, files in os.walk(top):
        for filename in files:
            _, ext = os.path.splitext(filename)
            if filename.endswith("~") or ext[1:] in ('pyc', 'pyo'):
                print "SKIPPING {!r}".format(filename)
                continue
            abs_path = os.path.abspath(os.path.join(root, filename))
            yield os.path.relpath(abs_path, start=top)


def mkdir_intermediate(path):
    abs_path = os.path.abspath(path)
    parts = abs_path.split(os.path.sep)
    current = ['']

    for append_me in parts[1:]:
        current.append(append_me)
        next_path = os.path.sep.join(current)
        if os.path.isdir(next_path):
            continue
        os.makedirs(next_path)


def compile_locales(top='locale', target_path=None):
    if target_path is None:
        target_path = top

    for po_file in glob.glob('{:s}/*.po'.format(top)):
        source = os.path.join(top, po_file)
        root, ext = os.path.splitext(po_file)
        trunk = os.path.basename(root)
        result = '{:s}/LC_MESSAGES/OpenWebif.mo'.format(trunk)
        target = os.path.join(target_path, result)
        command = COMPILE_PO_CALL_FMT.format(binary="msgfmt", target=target,
                                             source=source)
        target_dir = os.path.dirname(target)
        mkdir_intermediate(target_dir)
        rc = subprocess.call(command, shell=True)
        if rc != 0:
            raise ValueError(rc)


def compile_cheetah(target_path):
    command = COMPILE_CHEETAH_CALL_FMT.format(binary="cheetah",
                                              target=target_path)
    rc = subprocess.call(command, shell=True)
    if rc != 0:
        raise ValueError(rc)


def create_control():
    control_template = JINJA_ENV.get_template('control')
    control_content = control_template.render(**PACKAGE_META)
    control_path = os.path.join(PACKAGE_OUTPUT_PATH, "CONTROL")
    control_file = os.path.join(control_path, "control")

    if not os.path.isdir(PACKAGE_OUTPUT_PATH):
        os.makedirs(PACKAGE_OUTPUT_PATH)

    if not os.path.isdir(control_path):
        os.makedirs(control_path)

    with open(control_file, "wb") as target:
        target.write(control_content)


def create_tag(tag_file):
    data = {
        "upstream_version": PACKAGE_META['upstream_version'],
        "build_date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "owif_version": "OWIF 1.2.999"
    }

    with open(tag_file, "wb") as tgt:
        json.dump(data, tgt, indent=2)


def create_repo_conf(target_root, repo_config_filename='github_io.conf'):
    repo_config_template = JINJA_ENV.get_template(repo_config_filename)
    content = repo_config_template.render(**PACKAGE_META)
    repo_config_target_filename = os.path.join(
        target_root, repo_config_filename)

    with open(repo_config_target_filename, "wb") as target:
        target.write(content)


if __name__ == '__main__':
    try:
        os.environ["PYTHONOPTIMIZE"]
    except KeyError as keks:
        print("Please set PYTHONOPTIMIZE environment variable!")
        raise
    verbose = 0

    sources = './plugin'
    target_root = PACKAGE_OUTPUT_PATH
    target_path = os.path.join(
        target_root, TARGET_PATH_REL)
    tag_file = os.path.join(target_path, TAG_PATH_REL)

    if os.path.isdir(target_path):
        shutil.rmtree(target_path)

    if not os.path.isdir(target_root):
        os.makedirs(target_root)

    for rel_path in source_files(top=sources):
        source = os.path.join(sources, rel_path)
        target = os.path.join(target_path, rel_path)
        target_dir = os.path.dirname(target)
        if verbose > 0:
            print("{!r} -> {!r}".format(source, target))
        mkdir_intermediate(target_dir)
        shutil.copy(source, target_dir)

    compile_locales(os.path.abspath('locale'),
                    os.path.join(target_path, 'locale'))
    compile_cheetah(target_path)
    compileall.compile_dir(target_path, maxlevels=100, force=True)
    create_control()
    create_tag(tag_file)
    create_repo_conf(target_root=OUTPUT_PATH)

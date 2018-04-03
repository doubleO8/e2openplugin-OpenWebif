#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Helper functions for preparing OPKG package contents.
"""
import os
import shutil
import glob
import subprocess
import json
import datetime

from jinja2 import Environment, PackageLoader

from defaults import PACKAGE_OUTPUT_PATH, PACKAGE_META

COMPILE_PO_CALL_FMT = '{binary} -o "{target}" "{source}"'
COMPILE_CHEETAH_CALL_FMT = '{binary} compile -R "{target}"'
JINJA_ENV = Environment(loader=PackageLoader('pert_belly_hack', 'templates'))


def source_files(top):
    """
    Generator for paths of files to be included.

    Args:
        top (basestring): root path
    """
    for root, _, files in os.walk(top):
        for filename in files:
            _, ext = os.path.splitext(filename)
            if filename.endswith("~") or ext[1:] in ('pyc', 'pyo'):
                print "SKIPPING {!r}".format(filename)
                continue
            abs_path = os.path.abspath(os.path.join(root, filename))
            yield os.path.relpath(abs_path, start=top)


def mkdir_intermediate(path):
    """
    Create intermediate folders of *path*.

    Args:
        path (basestring): full path
    """
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
    """
    Run locale generator for `.po` files in *top*.

    Args:
        top: location of `.po` files
        target_path (basestring): (optional) path where generated `.mo` files will be stored  #NOQA
    """
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
    """
    Run cheetah template generator for *target_path*.

    Args:
        target_path (basestring): cheetah template path
    """
    command = COMPILE_CHEETAH_CALL_FMT.format(binary="cheetah",
                                              target=target_path)
    rc = subprocess.call(command, shell=True)
    if rc != 0:
        raise ValueError(rc)


def create_control():
    """
    Create OPKG's control meta file based on *PACKAGE_META* key/value pairs.
    """
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
    """
    Create tag meta file containing version and build information based on
    *PACKAGE_META* key/value pairs.

    Args:
        tag_file (basestring): tag file path
    """
    data = {
        "upstream_version": PACKAGE_META['upstream_version'],
        "build_date": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "owif_version": "OWIF 1.2.999"
    }

    with open(tag_file, "wb") as tgt:
        json.dump(data, tgt, indent=2)


def create_repo_conf(target_root, repo_config_filename='github_io.conf'):
    """
    Cerate OPKG repo configuration file based on *PACKAGE_META*
    key/value pairs.

    Args:
        target_root (basestring): output file path
        repo_config_filename (basestring): repo configuration basename

    Returns:
        basestring: repo configuration path
    """
    repo_config_template = JINJA_ENV.get_template(repo_config_filename)
    content = repo_config_template.render(**PACKAGE_META)
    repo_config_target_filename = os.path.join(
        target_root, repo_config_filename)

    with open(repo_config_target_filename, "wb") as target:
        target.write(content)

    return repo_config_target_filename


def create_package_repo_conf(target_root, repo_config_source,
                             repo_config_filename='package_name_here.conf'):
    """

    Args:
        target_root (basestring): path where configuration file will be copied to  #NOQA
        repo_config_source (basestring): repo configuration source
        repo_config_filename (basestring): repo configuration basename
    """
    package_etc_opkg = os.path.join(target_root, 'etc/opkg')
    package_repo_config = os.path.join(package_etc_opkg, repo_config_filename)
    mkdir_intermediate(package_etc_opkg)
    shutil.copy(repo_config_source, package_repo_config)

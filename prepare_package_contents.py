#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI tool: generate OPKG package and meta data.
"""
import os
import shutil
import compileall

from beppo.defaults import PACKAGE_OUTPUT_PATH, OUTPUT_PATH
from beppo.defaults import TARGET_PATH_REL, TAG_PATH_REL
from beppo.packaging import source_files, mkdir_intermediate
from beppo.packaging import compile_cheetah, compile_locales
from beppo.packaging import create_control, create_tag, create_repo_conf
from beppo.packaging import create_package_repo_conf

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
    repo_config_target_filename = create_repo_conf(target_root=OUTPUT_PATH)
    create_package_repo_conf(target_root=PACKAGE_OUTPUT_PATH,
                             repo_config_source=repo_config_target_filename)

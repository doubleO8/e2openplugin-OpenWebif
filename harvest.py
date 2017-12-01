#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import shutil
import json
import subprocess

from jinja2 import Environment, PackageLoader

from beppo.defaults import PACKAGE_META, OUTPUT_PATH, LATEST_OPK_PATH_REL
from beppo.defaults import PACKAGE_OUTPUT_PATH, TARGET_PATH_REL, TAG_PATH_REL


class HarvestKeitel(object):
    def __init__(self, *args, **kwargs):
        self.env = Environment(loader=PackageLoader('beppo', 'templates'))
        self.ghpages_output_path = kwargs.get(
            "ghpages_output_path", OUTPUT_PATH)
        self.package_output_path = kwargs.get(
            "package_output_path", PACKAGE_OUTPUT_PATH)
        opkg_filename_template = self.env.get_template('opkg_filename')
        self.package_source = opkg_filename_template.render(
            **PACKAGE_META).strip()
        if not os.path.isdir(self.ghpages_output_path):
            os.makedirs(self.ghpages_output_path)
        self.tag_data = self._load_tag()

    def _load_tag(self):
        tag_file = os.path.join(
            self.package_output_path, TARGET_PATH_REL, TAG_PATH_REL)
        with open(tag_file, "rb") as tag_src:
            tag_data = json.load(tag_src)
        return tag_data

    def harvest(self):
        self.copy_package()
        self.update_documentation()
        self.create_ghpages_index()
        self.create_ghpages_latest_package_link()

    def copy_package(self):
        tgt_filename = os.path.join(
            self.ghpages_output_path, os.path.basename(self.package_source))
        shutil.copy(self.package_source, tgt_filename)

    def create_ghpages_index(self):
        index_template = self.env.get_template('index.html')
        index_filename = os.path.join(self.ghpages_output_path, "index.html")
        index_content = {
            "files": [
                dict(
                    filename=os.path.basename(self.package_source),
                    description="latest release"),
                dict(
                    filename='flake8_report.txt',
                    description="flake8 report"),
                dict(
                    filename='jshint_report.txt',
                    description="JsHint report"),
                dict(
                    filename='github_io.conf',
                    description="opkg feed configuration file"),
                dict(
                    filename='doc/index.html',
                    description="documentation"),
            ],
            "meta": PACKAGE_META,
            "tag_data": self.tag_data,
        }

        with open(index_filename, "wb") as target:
            target.write(index_template.render(**index_content))

    def create_ghpages_latest_package_link(self):
        current_opk_link = os.path.join(
            self.ghpages_output_path, LATEST_OPK_PATH_REL)

        if os.path.islink(current_opk_link):
            os.unlink(current_opk_link)

        old_cwd = os.getcwd()
        os.chdir(self.ghpages_output_path)
        os.symlink(os.path.basename(self.package_source),
                   os.path.basename(current_opk_link))
        os.chdir(old_cwd)

    def update_documentation(self):
        subprocess.check_call("make html", cwd='./doc', shell=True)
        doc_target = os.path.join(self.ghpages_output_path, 'doc')

        if os.path.isdir(doc_target):
            shutil.rmtree(doc_target)

        shutil.copytree('./doc/build/html', doc_target)
        mr_hyde = "./doc/build/html/.nojekyll"
        with open(mr_hyde, "wb") as tgt:
            tgt.write("NO!")


if __name__ == '__main__':
    HARVEY = HarvestKeitel()
    HARVEY.harvest()

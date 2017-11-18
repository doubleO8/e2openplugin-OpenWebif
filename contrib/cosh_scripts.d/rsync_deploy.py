#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess

from coshed.coshed_config import CoshedConfigReadOnly

RSYNC_CALL_FMT = 'rsync {args} "{source}" "{destination}"'
coshfile = sys.argv[1]

cosh_cfg = CoshedConfigReadOnly(coshfile)
coshdir = os.path.dirname(coshfile)

for needed_key in ('rsync_source', 'rsync_destination', 'rsync_args'):
    if not cosh_cfg[needed_key]:
        sys.exit(1)

exclude_from_file = cosh_cfg['rsync_exclude_from']
if exclude_from_file and os.path.exists(exclude_from_file):
    cosh_cfg['rsync_args'].append('--exclude-from="{:s}"'.format(exclude_from_file))

call_cmd = RSYNC_CALL_FMT.format(
    source=cosh_cfg.rsync_source,
    destination=cosh_cfg.rsync_destination,
    args=' '.join(cosh_cfg.rsync_args)
)

print("About to call:")
print(call_cmd)

rc = subprocess.call(call_cmd, cwd=coshdir, shell=True)

print("# RC={:d}".format(rc))
sys.exit(rc)

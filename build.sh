#!/bin/sh
rm -rf ./pages_out
mkdir -p ./pages_out
python ./prepare_package_contents.py
./opkg-utils/opkg-build -O -o 0 -g 0 -Z gzip pack/
python ./harvest.py

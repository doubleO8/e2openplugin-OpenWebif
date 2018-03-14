#!/bin/sh
export PYTHONOPTIMIZE=yeah
rm -rf ./pages_out
mkdir -p ./pages_out
rm *.opk
python ./prepare_package_contents.py
./opkg-utils/opkg-build -O -o 0 -g 0 -Z gzip pack/
python ./harvest.py
./opkg-utils/opkg-make-index ./pages_out/ | tee ./pages_out/Packages
gzip ./pages_out/Packages
if [ -f cosh.json ]; then
    coshed-watcher.py -f cosh.json -u
fi

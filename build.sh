#!/bin/sh
export PYTHONOPTIMIZE=yeah

rm -rf pages_out
mkdir pages_out

cd pert_belly_hack-backend
pbh-clean
./build.sh
cd ..

cd pert_belly_hack-frontend-crap
pbh-clean
./build.sh
cd ..

cp -r pert_belly_hack-backend/pages_out/ pages_out/backend
cp -r pert_belly_hack-frontend-crap/pages_out/ pages_out/frontend-crap

./opkg-utils/opkg-make-index ./pages_out/ | tee ./pages_out/Packages
gzip ./pages_out/Packages

pbh-umbrella

if [ -f cosh.json ]; then
    coshed-watcher.py -f cosh.json -u
fi

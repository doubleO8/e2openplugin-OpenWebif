[![Build Status](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif.svg?branch=master)](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif)

# OpenWebif
OpenWebif is yet another web interface for Enigma2 based set-top boxes (STBs).

## Latest Package

The most recent package may be downloaded [here](https://doubleo8.github.io/e2openplugin-OpenWebif/latest.opk).

## Installation

```bash
# Remotely logged in via Telnet/SSH to enigma2 device

cd /tmp
init 4                                                              # graceful enigma2 shutdown
wget 'https://doubleo8.github.io/e2openplugin-OpenWebif/latest.opk' # fetching latest package
opkg install ./latest.opk                                           # installing latest package
init 3                                                              # start enigma2 again
```

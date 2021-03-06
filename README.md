
# pert_belly_hack
*pert_belly_hack* is yet another web interface for Enigma2 based set-top boxes.
It is a developer friendly fork of [OpenWebif](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif)
pursuing a different set of goals.

## Build Status

### Umbrella (OPKG reposiory)

[![Build Status](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif.svg?branch=master)](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif)

### Backend

[![Build Status](https://travis-ci.org/doubleO8/pert_belly_hack-backend.svg?branch=master)](https://travis-ci.org/doubleO8/pert_belly_hack-backend)

### Outdated Browser UI

[![Build Status](https://travis-ci.org/doubleO8/pert_belly_hack-frontend-crap.svg?branch=master)](https://travis-ci.org/doubleO8/pert_belly_hack-frontend-crap)

## Goals

* Create a Developer Friendly Web Interface for Enigma2 based set-top boxes.
  * ~~Clean Python Code (hopefully [PEP 8](https://www.python.org/dev/peps/pep-0008/) compliant some day)~~
  * ~~Clean and Valid ECMAScript Code~~
  * ~~[Unit Tests](https://doubleo8.github.io/e2openplugin-OpenWebif/nosetests.xml)~~ and ~~[Documentation](https://doubleo8.github.io/e2openplugin-OpenWebif/documentation/index.html)~~
  * ~~Separation of Code and Representation~~
* Provide ~~RESTful API~~ and access to ~~EPG event datasets~~, ~~timers~~, ~~recorded audio/video (dubbed *movie* elsewhere) items~~
* Support for multitier architecture, ~~reverse proxies~~ and client side rendering
* A Modern Web UI Implementation

## Cloning

```bash
git clone --recursive -j4 --depth 1 https://github.com/doubleO8/e2openplugin-OpenWebif
```

## Installation

It is recommended that one installs `pert belly hack` packages using the github hosted OPKG repository.

### Import OPKG repository / IPKG feed

Create or [download](https://doubleo8.github.io/e2openplugin-OpenWebif/pert_belly_hack.conf) `pert_belly_hack.conf`:

```bash
# Remotely logged in via SSH to enigma2 device

wget -q https://doubleo8.github.io/e2openplugin-OpenWebif/pert_belly_hack.conf \
-O /etc/opkg/pert_belly_hack.conf                                   # import repository
```

### Manual Installation after importing OPKG feed

```bash
opkg update                                                         # update list of available packages
opkg remove enigma2-plugin-extensions-openwebif                     # remove OpenWebif
opkg install pert-belly-hack-backend                                # upgrade or install package (backend)
opkg install pert-belly-hack-frontend-crap                          # upgrade or install package (frontend)
init 4                                                              # graceful enigma2 shutdown
sleep 1                                                             # wait a bit
init 3                                                              # start enigma2 again
```

## Online Documentation

The Online Documentation for the backend is available at [doubleo8.github.io/e2openplugin-OpenWebif/backend/documentation/](https://doubleo8.github.io/e2openplugin-OpenWebif/backend/documentation/index.html).

* [HTTP Routing Table](https://doubleo8.github.io/e2openplugin-OpenWebif/backend/documentation/http-routingtable.html) *work in progress*
* [Enigma2 WebInterface API](https://doubleo8.github.io/e2openplugin-OpenWebif/backend/documentation/e2webinterface_api.html) *work in progress*
* [RESTful API](https://doubleo8.github.io/e2openplugin-OpenWebif/backend/documentation/restful_api.html) *work in progress*

## Dropped *OpenWebif* Features

Some features of the original plugin have been removed:

* TLS/SSL support
* package management
* "mobile" version
* bouquet editor
* support for shellinaboxd
* support for lcd4linux web portions
* image files of enigma devices
* themes
* image files and HTML maps of remotes

[![Build Status](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif.svg?branch=master)](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif)

# [INSERT NAME HERE]
*[INSERT NAME HERE]* is yet another web interface for Enigma2 based set-top boxes.
It is a developer friendly fork of [OpenWebif](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif)
pursuing a different set of goals.

## Goals

* Create a Developer Friendly Web Interface for Enigma2 based set-top boxes.
  * ~~Clean Python Code (hopefully [PEP 8](https://www.python.org/dev/peps/pep-0008/) compliant some day)~~
  * Clean and Valid ECMAScript Code
  * Unit Tests and ~~[Documentation](https://doubleo8.github.io/e2openplugin-OpenWebif/documentation/index.html)~~
  * Separation of Code and Representation
* Provide RESTful API and access to EPG events, ~~timers~~, ~~recorded audio/video (dubbed *movie*) items~~
* Support for multitier architecture, reverse proxies and client side rendering
* A Modern Web UI Implementation
* Find a Smashing New Project Name

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

# Latest Package

The most recent package may be downloaded [here](https://doubleo8.github.io/e2openplugin-OpenWebif/latest.opk).

## Installation

```bash
# Remotely logged in via SSH to enigma2 device

cd /tmp
init 4                                                              # graceful enigma2 shutdown
wget 'https://doubleo8.github.io/e2openplugin-OpenWebif/latest.opk' # fetching latest package
opkg install ./latest.opk                                           # installing latest package
init 3                                                              # start enigma2 again
```

### opkg feed

Create or [download](https://doubleo8.github.io/e2openplugin-OpenWebif/github_io.conf) `/etc/opkg/github_io.conf`:

```
src/gz githubio https://doubleo8.github.io/e2openplugin-OpenWebif
```

```bash
# Remotely logged in via SSH to enigma2 device

wget -q https://doubleo8.github.io/e2openplugin-OpenWebif/github_io.conf \
-O /etc/opkg/github_io.conf                                         # import repository
opkg update                                                         # update list of available packages
opkg install enigma2-plugin-extensions-openwebif                    # upgrade or install package
init 4                                                              # graceful enigma2 shutdown
sleep 1                                                             # wait a bit
init 3                                                              # start enigma2 again
```

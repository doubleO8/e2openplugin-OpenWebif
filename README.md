[![Build Status](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif.svg?branch=master)](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif)

# OpenWebif
OpenWebif is an open source web interface for Enigma2 based set-top boxes (STBs).

## License
Licensed under the GNU General Public License, Version 3. See [LICENSE](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/LICENSE.txt) for more details.

## Latest Package

The most recent package may be downloaded [here](https://doubleo8.github.io/e2openplugin-OpenWebif/).

### Installation

```bash
# Remotely logged in via Telnet/SSH to enigma2 device
cd /tmp
init 4                        # graceful enigma2 shutdown
# fetching -- wget '<URL of .ipk file>'
# example:
wget 'https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/gh-pages/enigma2-plugin-extensions-openwebif_1.2.7-e2openpluginsgit20171014_all.ipk'
# installing -- opkg install <.ipk file>
# example:
opkg install ./enigma2-plugin-extensions-openwebif_1.2.7-e2openpluginsgit20171014_all.ipk
init 3                        # start enigma2 again
```

## Development Information

See  [commit log](https://github.com/doubleO8/e2openplugin-OpenWebif/commits/master).

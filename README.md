[![Build Status](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif.svg?branch=master)](https://travis-ci.org/doubleO8/e2openplugin-OpenWebif)

# OpenWebif
OpenWebif is an open source web interface for Enigma2 based set-top boxes (STBs).

## License
Licensed under the GNU General Public License, Version 3. See [LICENSE](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/blob/master/LICENSE.txt) for more details.

## Latest Package

The most recent package may be downloaded [here](https://github.com/E2OpenPlugins/e2openplugin-OpenWebif/tree/gh-pages) (ipk package).

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

### Dependencies
The following additional packages need to be installed:

    python-pprint
    python-cheetah
    python-json
    python-unixadmin
    python-misc
    python-twisted-web
    python-pyopenssl
    python-compression
    python-ipaddress

_(Dependencies should be handled by using ipkg/opkg packages)_

### Compiling JavaScript Files

The javascipt source files inside of /sourcefiles/js needs to compress via UglifyJS2 on http://refresh-sf.com/.
You need to increase the version and write down your modification description inside of the source file.
The compressed file have the following syntax : xx-<version>.min.js

### Compiling CSS Files

The script `contrib/inotify_watcher.py` is used for compiling CSS files on
the developers host using [Sass](http://sass-lang.com/) . On linux you need to
have installed a package providing  `inotifywait` and a version that actually
supports inotify if one wants automatic compiling of CSS files on source
directory changes (For debian based distributions this would be `inotify-tools`).

Mac and Windows do not have inotify support thus the automatic compiling will
not work (yet). But if you installed Sass (see http://sass-lang.com/install) and
the `scss` binary/script is in your `PATH` calling
`contrib/inotify_watcher.py --force-update` should work.
Alternatively you may define environment variable `SCSS` in order to point to
the location of the scss binary/script.

Base command is

    scss -t compressed --unix-newlines --sourcemap=none "in.scss":"out.css"

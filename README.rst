pert_belly_hack
===============

Packaging helper for preparing the contents of an OPKG file containing
a web interface for enigma2 devices. Also generates contents for github
pages.

Source Code
-----------

https://github.com/doubleO8/e2openplugin-OpenWebif/

Documentation
-------------

https://doubleo8.github.io/e2openplugin-OpenWebif/documentation/packaging.html

Project Page
------------

https://doubleo8.github.io/e2openplugin-OpenWebif/

Usage
=====

.. code-block:: sh

    # create OPKG contents in subfolder ``./pack/``
    python ./prepare_package_contents.py
    # example call for generating ``.opk`` file:
    ./opkg-utils/opkg-build -O -o 0 -g 0 -Z gzip pack/

.. code-block:: sh

    # create github pages content in ``./pages_out/``
    python ./harvest.py

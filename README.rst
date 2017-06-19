==================
Pandora API Client
==================

.. image:: https://img.shields.io/pypi/v/pydora.svg
    :target: https://pypi.python.org/pypi/pydora

.. image:: https://img.shields.io/travis/mcrute/pydora.svg
    :target: https://travis-ci.org/mcrute/pydora

This code is licensed under the MIT license.

This is a reasonably complete implementation of the Pandora API that supports
Python 2 and 3. It does not implement any of the undocumented features and does
not implement most of the account management features as they are not terribly
useful.

Keys or passwords for Pandora are **not** provided in this repo, you'll have to
`go get those <http://6xq.net/playground/pandora-apidoc/json/partners/#partners>`_
for yourself. Make something awesome with this library, don't abuse Pandora,
that's not cool.

The easy entry-point for programmatic use is
``pandora.clientbuilder.PydoraConfigFileBuilder``. All programmatic APIs are in
the ``pandora`` package. The remainder of this README is targeted at users of
the ``pydora`` command-line player.

Installing
==========
Installing is as simple as using pip and running the built-in configuration
command to create a ``~/.pydora.cfg`` file. If you already have a `PianoBar
<http://6xq.net/projects/pianobar/>`_ config file pydora will automatically use
that. ::

    $ pip install pydora
    $ pydora-configure

On Ubuntu install `vlc` or `vlc`::

    # apt-get install vlc

To install VLC on Mac OS X visit the `VLC site
<https://www.videolan.org/vlc/>`_ to download ``VLC.app``, then drag-and-drop
the bundle into your ``/Applications`` folder. pydora will auto-detect this.

Audio Output Backend
====================
The ``pydora`` player does not directly support audio output but instead relies
upon external audio output backends. The two supported backends are VLC and
mpg123. The main difference between the two backends is the supported file
formats. VLC supports a vast array of codecs, including MP3 and AAC, the two
formats that Pandora uses. mpg123 on the other hand supports only MP3. As of
2017 Pandora has started to prefer AAC files over MP3 which necessitates VLC.
The ``pydora`` player will try to auto-detect whatever player exists on your
system, prefering VLC, and will use that audio output backend. If you notice a
lot of skipping in a playlist consider installing VLC.

Simple Player
=============
Included is ``pydora``, a simple Pandora stream player that runs at the command
line. It requires that mpg123 or VLC be installed with HTTP support as well as
a settings file (example below) located in ``~/.pydora.cfg``. Alternatively an
environment variable ``PYDORA_CFG`` can point to the path of the config file.

The player only supports basic functionality for now. It will display a station
list, allow listening to any station, basic feeback and bookmarking are also
supported. The player starts an mpg123 or VLC process in remote control mode
and feeds commands to it. It does not download any music but rather streams
them directly from Pandora.

When playing the following keys work (press enter afterwards):

* n  - next song
* p  - pause or resume song
* s  - station list (stops song)
* d  - thumbs down track
* u  - thumbs up track
* b  - bookmark song
* a  - bookmark artist
* S  - sleep song
* Q  - quit program
* vu - volume up
* vd - volume down
* ?  - display help

Note that volume control is currently only supported with the VLC back-end.

Sample Config File
==================
::

    [api]
    api_host = hostname
    encryption_key = key
    decryption_key = key
    username = partner username
    password = partner password
    device = key
    default_audio_quality = mediumQuality

    [user]
    username = your username
    password = your password

**default_audio_quality**
  Default audio quality to request from the API; can be one of `lowQuality`,
  `mediumQuality` (default), or `highQuality`. If the preferred audio quality
  is not available for the device specified, then the next-highest bitrate
  stream that Pandora supports for the chosen device will be used.

Pandora API Spec and Partner Keys
=================================
The built-in ``pydora-configure`` script can be run to create a configuration
file if you don't already have one. This will download the keys from the link
below and pick a suitable one. If you're interested in the underlying API or
need to download the keys yourself you can find them at the link below.

* `API Spec <http://6xq.net/playground/pandora-apidoc/>`_
* `Partner Keys <http://6xq.net/playground/pandora-apidoc/json/partners/#partners>`_

Contributing
============
If you would like to contribute to Pydora please visit the project's
`GitHub page <https://github.com/mcrute/pydora>`_ and open a pull request with
your changes. To have the best experience contributing, please:

* Don't break backwards compatibility of public interfaces
* Write tests for your new feature/bug fix
* Ensure that existing tests pass
* Update the readme/docstrings, if necessary
* Follow the coding style of the current code-base
* Ensure that your code is PEP8 compliant
* Validate that your changes work with Python 2.7+ and 3.3+

All code is reviewed before acceptance and changes may be requested to better
follow the conventions of the existing API.

The build system runs ``python setup.py validate`` on all supported Python
versions. You can, and should, run this on your pull request before submitting.

Contributors
============
* Mike Crute (`mcrute <https://github.com/mcrute>`_)
* John Cass (`jcass77 <https://github.com/jcass77>`_)
* Thomas Weißschuh (`t-8c <https://github.com/t-8ch>`_)

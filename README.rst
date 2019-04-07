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

As of 1.11.0 users of Python 3.4+ no longer require a native dependency and can
use this package in its pure Python form. Users of older versions of Python
will require `cryptography <https://pypi.python.org/pypi/cryptography>`_. This
is configured automatically when pydora is installed.

Programatic Use
===============
The pydora distribution contains two python packages. The ``pandora`` package
is the API for interacting with the Pandora service. The ``pydora`` package is
a very small reference implementation of using the API to drive a command line
player. If you're interested in the command line skip this section and read
Installing below to get started.

**NOTE:** This package uses semantic versioning. The API is stable within a
major version release. Please constrain your dependencies to major versions.
For example, to depend on version 1.x use this line in your setup.py
``install_requires``::

    pydora>=1,<2

The easiest way to get started is by using the ``pandora.clientbuilder``
package. This package contains a set of factories that can be used to build a
Pandora client with some configuration.  The classes in the package that end in
``Builder`` are the factories and the rest of the classes are implementation
details. All of the builders will return an instance of
``pandora.client.APIClient`` that is completely configured and ready for use in
your program.

If you have an existing program and would like to connect to Pandora the
easiest way is to use the ``SettingsDictBuilder`` class like so::

    client = SettingsDictBuilder({
        "DECRYPTION_KEY": "see_link_above",
        "ENCRYPTION_KEY": "see_link_above",
        "PARTNER_USER": "see_link_above",
        "PARTNER_PASSWORD": "see_link_above",
        "DEVICE": "see_link_above",
    }).build()

    client.login("username", "password")

At this point the client is ready for use, see ``pandora.client.APIClient`` for
a list of methods that can be called. All responses from the API will return
Python objects from the ``pandora.models.pandora`` package or raise exceptions
from ``pandora.errors``

For a more functional example look at the file ``pydora/player.py`` which shows
how to use the API in a simple command line application.

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

Remote VLC Backend
------------------
It is also possible to remotely control a copy of VLC running on another
machine if you're unable or unwilling to install Pydora on your playback
machine. To do this start VLC on the remote machine with the ``rc-host`` option
set. For example::

    vlc -I rc --advanced --rc-host=0.0.0.0:1234

Once VLC is running start Pydora with the ``vlc-net`` option and specify the
remote host and port that VLC is listening on. For example::

    pydora --vlc-net 192.168.0.12:1234

Pydora will now send all audio playback requests to the remote VLC. It does
this using a text control protocol; all audio data is streamed directly from
the internet to VLC and is not passed over the pydora control channel. Because
of this it is possible for the control channel to run over a very low bandwidth
connection.

**Note**: VLC doesn't provide any security so anyone on the network will be
able to control VLC. It is generally safer to bind VLC to ``127.0.0.1`` and use
something like SSH forwarding to securely forward the port to a remote host but
that's outside of the scope of this README.

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
See `CONTRIBUTING <https://github.com/mcrute/pydora/blob/master/CONTRIBUTING.rst>`_

Contributors
============
* Mike Crute (`@mcrute <https://github.com/mcrute>`_)
* John Cass (`@jcass77 <https://github.com/jcass77>`_)
* Thomas Weißschuh (`@t-8c <https://github.com/t-8ch>`_)
* Skybound1 (`@Skybound1 <https://github.com/Skybound1>`_)
* Hugo (`@hugovk <https://github.com/hugovk>`_)

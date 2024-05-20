==================
Pandora API Client
==================

.. image:: https://img.shields.io/pypi/v/pydora.svg
    :target: https://pypi.python.org/pypi/pydora

.. image:: https://github.com/mcrute/pydora/workflows/build/badge.svg
    :target: https://github.com/mcrute/pydora/actions?query=workflow%3Abuild

This code is licensed under the MIT license. The code is maintained on `GitHub
<https://github.com/mcrute/pydora>`_.

This is a reasonably complete implementation of the Pandora API in pure Python
that supports Python 3.5+. It contains a complete implementation of the core
radio features but does not implement account management or Pandora Plus
functionality; pull requests adding that functionality are welcomed from anyone
needing those features.

Keys or passwords for Pandora are **not** provided in this repo, you'll have to
`go get those <http://6xq.net/playground/pandora-apidoc/json/partners/#partners>`_
for yourself. Make something awesome with this library, don't abuse Pandora,
that's not cool.

Project Complete
================
This project **is actively maintained** but the author considers it to be both
stable and complete. There will be very few new changes initiated by the author
outside of bug fixes and security updates.

If you run into a problem, file an issue and we'll respond. Pull requests for
new features and fixes will be reviewed and accepted if they meet our criteria
for stability, see below for contributing instructions.

Compatibility
=============
This is the ``2.x`` series which supports only Python 3.8+. For older versions
of Python please use the |1.x|_ series. The |1.x|_ series is no longer
maintained but pull requests to fix bugs are still welcomed.

This package uses semantic versioning. The API is guaranteed to be stable
within a major version release. Please constrain your dependencies to major
versions. For example, to depend on version ``2.x`` use this line in your
setup.py ``install_requires``::

    pydora>=2,<3

Installing
==========
Installing is as simple as using pip and running the built-in configuration
command to create a ``~/.pydora.cfg`` file. If you already have a `PianoBar
<http://6xq.net/projects/pianobar/>`_ config file Pydora will automatically use
that. ::

    $ pip install pydora
    $ pydora-configure

On Ubuntu install `vlc` or `vlc`::

    # apt-get install vlc

To install VLC on Mac OS X visit the `VLC site
<https://www.videolan.org/vlc/>`_ to download ``VLC.app``, then drag-and-drop
the bundle into your ``/Applications`` folder. Pydora will auto-detect this.

Audio Output Back-end
=====================
The ``pydora`` player does not directly support audio output but instead relies
upon external audio output back-ends. The two supported back-ends are VLC and
mpg123. The main difference between the two back-ends is the supported file
formats. VLC supports a vast array of codecs, including MP3 and AAC, the two
formats that Pandora uses. mpg123 on the other hand supports only MP3. As of
2017 Pandora has started to prefer AAC files over MP3 which necessitates VLC.
The ``pydora`` player will try to auto-detect whatever player exists on your
system, preferring VLC, and will use that audio output back-end. If you notice
a lot of skipping in a playlist consider installing VLC.

Remote VLC Back-end
-------------------
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
the internet to VLC and is not passed over the Pydora control channel. Because
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
list, allow listening to any station, basic feedback and bookmarking are also
supported. The player starts an mpg123 or VLC process in remote control mode
and feeds commands to it. It does not download any music but rather streams
them directly from Pandora.

When playing the following keys work (press enter afterwards):

* ``n``  - next song
* ``p``  - pause or resume song
* ``s``  - station list (stops song)
* ``d``  - thumbs down track
* ``u``  - thumbs up track
* ``b``  - bookmark song
* ``a``  - bookmark artist
* ``S``  - sleep song
* ``Q``  - quit program
* ``vu`` - volume up
* ``vd`` - volume down
* ``?``  - display help

**Note**: volume control is currently only supported with the VLC back-end.

Sample Config File
==================
The built-in ``pydora-configure`` script can be run to create a configuration
file automatically if you don't already have one. This will download the keys
from the link below and pick a suitable one when writing the config file. If
you want to create the config file manually the format is:
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
  is not available for the device specified, then the next-highest bit-rate
  stream that Pandora supports for the chosen device will be used.

Programmatic Use
================
The Pydora distribution contains two python packages. The |pandora package|_
is the API for interacting with the Pandora service. The |pydora package|_ is
a very small reference implementation of using the API to drive a command line
player. If you're interested in the command line skip this section and read
Installing below to get started.

The easiest way to get started is by using the |pandora.clientbuilder|_
package. This package contains a set of factories that can be used to build a
Pandora client with some configuration. The classes in the package that end in
``Builder`` are the factories and the rest of the classes are implementation
details. All of the builders will return an instance of
|pandora.client.APIClient|_ that is completely configured and ready for use in
your program.

If you have an existing program and would like to connect to Pandora the
easiest way is to use the |SettingsDictBuilder|_ class like so::

    client = SettingsDictBuilder({
        "DECRYPTION_KEY": "see_link_above",
        "ENCRYPTION_KEY": "see_link_above",
        "PARTNER_USER": "see_link_above",
        "PARTNER_PASSWORD": "see_link_above",
        "DEVICE": "see_link_above",
    }).build()

    client.login("username", "password")

At this point the client is ready for use, see |pandora.client.APIClient|_ for
a list of methods that can be called. All responses from the API will return
Python objects from the |pandora.models.pandora|_ package or raise exceptions
from |pandora.errors|_

For a more functional example look at the file |pydora/player.py|_ which shows
how to use the API in a simple command line application.

Pandora API Spec and Partner Keys
=================================
If you're interested in the underlying API or need to download the keys
yourself you can find more details at the links below. This documentation is
community maintained and not official.

* `API Spec <http://6xq.net/playground/pandora-apidoc/>`_
* `Partner Keys <http://6xq.net/playground/pandora-apidoc/json/partners/#partners>`_

Contributing
============
See `CONTRIBUTING <https://github.com/mcrute/pydora/blob/master/CONTRIBUTING.rst>`_

Contributors
============
Thanks to the contributors who make Pydora possible by adding features and
fixing bugs. List is organized by date of first contribution.

* Mike Crute (`@mcrute <https://github.com/mcrute>`_)
* John Cass (`@jcass77 <https://github.com/jcass77>`_)
* Thomas Weißschuh (`@t-8c <https://github.com/t-8ch>`_)
* Skybound1 (`@Skybound1 <https://github.com/Skybound1>`_)
* Hugo (`@hugovk <https://github.com/hugovk>`_)
* mspencer92 (`@mspencer92 <https://github.com/mspencer92>`_)

.. |1.x| replace:: ``1.x``
.. _1.x: https://github.com/mcrute/pydora/tree/1.x

.. |pandora package| replace:: ``pandora`` package
.. _pandora package: https://github.com/mcrute/pydora/tree/master/pandora

.. |pydora package| replace:: ``pydora`` package
.. _pydora package: https://github.com/mcrute/pydora/tree/master/pydora

.. |pandora.clientbuilder| replace:: ``pandora.clientbuilder``
.. _pandora.clientbuilder: https://github.com/mcrute/pydora/blob/master/pandora/clientbuilder.py

.. |pandora.client.APIClient| replace:: ``pandora.client.APIClient``
.. _pandora.client.APIClient: https://github.com/mcrute/pydora/blob/master/pandora/client.py#L98

.. |SettingsDictBuilder| replace:: ``SettingsDictBuilder``
.. _SettingsDictBuilder: https://github.com/mcrute/pydora/blob/master/pandora/clientbuilder.py#L136

.. |pandora.models.pandora| replace:: ``pandora.models.pandora``
.. _pandora.models.pandora: https://github.com/mcrute/pydora/tree/master/pandora/models

.. |pandora.errors| replace:: ``pandora.errors``
.. _pandora.errors: https://github.com/mcrute/pydora/blob/master/pandora/errors.py

.. |pydora/player.py| replace:: ``pydora/player.py``
.. _pydora/player.py: https://github.com/mcrute/pydora/blob/master/pydora/player.py

==================
Pandora API Client
==================

This code is licensed under the MIT license.

This is a reasonably complete implementation of the Pandora API. It does not
implement any of the undocumented features and does not implement most of the
account management features as they were deemed not terribly useful.

I don't provide any keys or passwords for Pandora in this repo, you'll have to
go get those for yourself. Make something awesome with this library, don't
abuse Pandora, that's not cool.

 * API Spec from: http://pan-do-ra-api.wikia.com/wiki/Json/5
 * Keys at: http://pan-do-ra-api.wikia.com/wiki/Json/5/partners

Simple Player
=============
Included is ``pydora``, a simple Pandora stream player that runs at the command
line. It requires that mpg123 be installed with HTTP support as well as a
settings file (example below) located in ``~/.pydora.cfg``. Alternatively an
environment variable ``PYDORA_CFG`` can point to the path of the config file.

The player only supports basic functionality for now. It will display a station
list, allow listening to any station, basic feeback and bookmarking are also
supported. The player starts an mpg123 process in remote control mode and feeds
commands to it. It does not download any music but rather streams them directly
from Pandora.

When playing the following keys work (press enter afterwards):

 * n - next song
 * p - pause or resume song
 * s - station list (stops song)
 * d - thumbs down track
 * u - thumbs up track
 * b - bookmark song
 * a - bookmark artist
 * S - sleep song
 * Q - quit program
 * ? - display help

sample config::

    [api]
    encryption_key = key
    decryption_key = key
    username = partner username
    password = partner password
    device = key

    [user]
    username = your username
    password = your password

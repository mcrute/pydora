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

Example::

    >>> SETTINGS = {
    ...     'ENCRYPTION_KEY': '',
    ...     'DECRYPTION_KEY': '',
    ...     'USERNAME': '',
    ...     'PASSWORD': '',
    ...     'DEVICE': '',
    ... }
    >>> client = APIClient.from_settings_dict(SETTINGS)
    >>> client.login("username", "password")


Simple Player
=============
Contained in `simple_player.py` is a simple Pandora stream player that runs at
the command line. It requires that mpg123 be installed with HTTP support as
well as a `settings.py` file that contains `SETTINGS` (per above), `USERNAME`
and `PASSWORD` which correspond to your Pandora credentials.

The player only supports simple playback for now. It will display a station
list and allow listening to any station but no writeable operations are
supported. The player starts an mpg123 process in remote control mode and feeds
commands to it. It does not download any music but rather streams them directly
from Pandora.

When playing the following keys work (press enter afterwards):

 * n - next song
 * p - pause or resume song
 * s - station list (stops song)
 * Q - quit program

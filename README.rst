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

API Spec from: http://pan-do-ra-api.wikia.com/wiki/Json/5
Keys at: http://pan-do-ra-api.wikia.com/wiki/Json/5/partners

Example::

    >>> encryptor = Encryptor("in_key", "out_key")
    >>> transport = APITransport(encryptor)
    >>> client = APIClient(transport, "partner", "parner_pass", "device")
    >>> client.login("username", "password")
    >>> stations = client.get_station_list()

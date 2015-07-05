"""
Pandora API Client

This is a reasonably complete implementation of the Pandora API. It does not
implement any of the undocumented features and does not implement most of the
account management features as they were deemed not terribly useful.

API Spec from: http://6xq.net/playground/pandora-apidoc/
Keys at: http://6xq.net/playground/pandora-apidoc/json/partners/#partners
"""

DEFAULT_API_HOST = "tuner.pandora.com/services/json/"

from .transport import APITransport, Encryptor
from .client import BaseAPIClient, APIClient

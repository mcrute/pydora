"""
Pandora API Client

This is a reasonably complete implementation of the Pandora API. It does not
implement any of the undocumented features and does not implement most of the
account management features as they were deemed not terribly useful.

API Spec from: http://6xq.net/playground/pandora-apidoc/
Keys at: http://6xq.net/playground/pandora-apidoc/json/partners/#partners
"""

from .client import BaseAPIClient, APIClient  # noqa: F401
from .transport import APITransport, Encryptor, DEFAULT_API_HOST  # noqa: F401

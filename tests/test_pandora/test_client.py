from unittest import TestCase

from pandora.client import BaseAPIClient
from pandora.transport import APITransport
from pandora.errors import InvalidAuthToken
from pandora.py2compat import Mock, MagicMock, call


class TestCallingAPIClient(TestCase):

    def test_call_should_retry_on_token_error(self):
        transport = Mock(side_effect=[InvalidAuthToken(), None])

        client = BaseAPIClient(transport, None, None, None)
        client._authenticate = Mock()

        client.login("foo", "bar")
        client("method")

        client._authenticate.assert_called_with()
        transport.assert_has_calls([call("method"), call("method")])

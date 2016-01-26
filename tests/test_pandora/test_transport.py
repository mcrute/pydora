import time
from unittest import TestCase
from pandora.errors import InvalidAuthToken, PandoraException

from pandora.py2compat import Mock, call

from tests.test_pandora.test_clientbuilder import TestSettingsDictBuilder


class SysCallError(Exception):
    pass


class TestTransport(TestCase):

    def test_call_should_retry_max_times_on_sys_call_error(self):
        with self.assertRaises(SysCallError):
            client = TestSettingsDictBuilder._build_minimal()

            time.sleep = Mock()
            client.transport._make_http_request = Mock(
                    side_effect=SysCallError("error_mock"))
            client.transport._start_request = Mock()

            client("method")

        client.transport._start_request.assert_has_calls([call("method")])
        assert client.transport._start_request.call_count == 3

    def test_call_should_not_retry_for_pandora_exceptions(self):
        with self.assertRaises(PandoraException):
            client = TestSettingsDictBuilder._build_minimal()

            time.sleep = Mock()
            client.transport._make_http_request = Mock(
                    side_effect=PandoraException("error_mock"))
            client.transport._start_request = Mock()

            client("method")

            client.transport._start_request.assert_has_calls([call("method")])
            assert client.transport._start_request.call_count == 1

    def test_call_should_retry_if_auth_token_expired(self):
        with self.assertRaises(InvalidAuthToken):
            client = TestSettingsDictBuilder._build_minimal()

            time.sleep = Mock()
            client.transport._make_http_request = Mock(
                    side_effect=InvalidAuthToken("error_mock"))
            client.transport._start_request = Mock()

            client._authenticate = Mock()

            client("method")

            client.transport._start_request.assert_has_calls([call("method")])
            assert client.transport._start_request.call_count == 2
            assert client._authenticate.call_count == 1

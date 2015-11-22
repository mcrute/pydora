from unittest import TestCase

from pandora.client import APIClient, BaseAPIClient
from pandora.errors import InvalidAuthToken
from pandora.py2compat import Mock, MagicMock, call, patch


class TestCallingAPIClient(TestCase):

    def test_call_should_retry_on_token_error(self):
        transport = Mock(side_effect=[InvalidAuthToken(), None])

        client = BaseAPIClient(transport, None, None, None)
        client._authenticate = Mock()

        client.login("foo", "bar")
        client("method")

        client._authenticate.assert_called_with()
        transport.assert_has_calls([call("method"), call("method")])

    def test_get_params_dict_ad_support_enabled(self):
        transport = Mock(side_effect=[InvalidAuthToken(), None])

        reg_dict = dict(x=1, y=2)
        ad_dict = dict(z=3)

        client = BaseAPIClient(transport, None, None, None, None, True)
        result_dict = client.get_params_dict(reg_dict, ad_dict)

        assert 'z' in result_dict

    def test_get_params_dict_ad_support_disabled(self):
        transport = Mock(side_effect=[InvalidAuthToken(), None])

        reg_dict = dict(x=1, y=2)
        ad_dict = dict(z=3)

        client = BaseAPIClient(transport, None, None, None, None, False)
        result_dict = client.get_params_dict(reg_dict, ad_dict)

        assert not 'z' in result_dict

    def test_ad_support_enabled_parameters(self):
        with patch.object(APIClient, '__call__') as playlist_mock:
            transport = Mock(side_effect=[InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None, True)
            client._authenticate = Mock()

            client.get_playlist('mock_token')

            playlist_mock.assert_has_calls([call("station.getPlaylist",
                                             audioAdPodCapable=True,
                                             includeTrackLength=True,
                                             stationToken='mock_token',
                                             xplatformAdCapable=True)])

    def test_ad_support_disabled_parameters(self):
        with patch.object(APIClient, '__call__') as playlist_mock:
            transport = Mock(side_effect=[InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None, False)
            client._authenticate = Mock()

            client.get_playlist('mock_token')

            playlist_mock.assert_has_calls([call("station.getPlaylist",
                                             includeTrackLength=True,
                                             stationToken='mock_token')])

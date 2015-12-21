from unittest import TestCase

from pandora.client import APIClient, BaseAPIClient
from pandora.errors import InvalidAuthToken
from pandora.py2compat import Mock, MagicMock, call, patch


class TestAPIClientLogin(TestCase):

    class StubTransport(object):

        API_VERSION = None

        partner = None
        user = None

        FAKE_PARTNER = object()
        FAKE_USER = object()

        def __call__(self, method, **params):
            if method == "auth.partnerLogin":
                return self.FAKE_PARTNER
            elif method == "auth.userLogin":
                return self.FAKE_USER
            else:
                raise AssertionError("Invalid call")

        def set_partner(self, partner):
            self.partner = partner

        def set_user(self, user):
            self.user = user

    def test_login(self):
        transport = self.StubTransport()
        client = BaseAPIClient(transport, None, None, None)
        client.login("foobear", "secret")

        self.assertEqual("foobear", client.username)
        self.assertEqual("secret", client.password)
        self.assertIs(self.StubTransport.FAKE_USER, transport.user)
        self.assertIs(self.StubTransport.FAKE_PARTNER, transport.partner)


class TestCallingAPIClient(TestCase):

    def test_call_should_retry_on_token_error(self):
        transport = Mock(side_effect=[InvalidAuthToken(), None])

        client = BaseAPIClient(transport, None, None, None)
        client._authenticate = Mock()

        client.login("foo", "bar")
        client("method")

        client._authenticate.assert_called_with()
        transport.assert_has_calls([call("method"), call("method")])

    def test_ad_support_enabled_parameters(self):
        with patch.object(APIClient, '__call__') as playlist_mock:
            transport = Mock(side_effect=[InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            client.get_playlist('mock_token')

            playlist_mock.assert_has_calls([call("station.getPlaylist",
                                             audioAdPodCapable=True,
                                             includeTrackLength=True,
                                             stationToken='mock_token',
                                             xplatformAdCapable=True)])


class TestGettingQualities(TestCase):

    def test_with_invalid_quality_returning_all(self):
        result = BaseAPIClient.get_qualities("foo", True)
        self.assertEqual(BaseAPIClient.ALL_QUALITIES, result)

    def test_with_invalid_quality_returning_none(self):
        result = BaseAPIClient.get_qualities("foo", False)
        self.assertEqual([], result)

    def test_with_valid_quality(self):
        result = BaseAPIClient.get_qualities(
                BaseAPIClient.MED_AUDIO_QUALITY, False)

        expected = [
                BaseAPIClient.LOW_AUDIO_QUALITY,
                BaseAPIClient.MED_AUDIO_QUALITY]

        self.assertEqual(expected, result)


class TestGettingAds(TestCase):

    mock_ad_metadata_result = {
        'audioUrlMap': {
            'mediumQuality': {
                'audioUrl': 'mock_med_url', 'bitrate': '64', 'protocol': 'http', 'encoding': 'aacplus'
            },
            'highQuality': {
                'audioUrl': 'mock_high_url', 'bitrate': '64', 'protocol': 'http', 'encoding': 'aacplus'
            },
            'lowQuality': {
                'audioUrl': 'mock_low_url', 'bitrate': '32', 'protocol': 'http', 'encoding': 'aacplus'}},
            'clickThroughUrl': 'mock_click_url',
            'imageUrl': 'mock_img_url',
            'companyName': '',
            'title': '',
            'trackGain': '0.0',
            'adTrackingTokens': ['mock_token_1', 'mock_token_2']
    }

    def test_get_ad_item_(self):
        with patch.object(APIClient, '__call__', return_value=self.mock_ad_metadata_result) as ad_metadata_mock:
            transport = Mock(side_effect=[InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            ad_item = client.get_ad_item('mock_id', 'mock_token')
            assert ad_item.station_id == 'mock_id'

            ad_metadata_mock.assert_has_calls([call("ad.getAdMetadata",
                                                      adToken='mock_token',
                                                      returnAdTrackingTokens=True,
                                                      supportAudioAds=True)])

    def test_get_ad_item_with_no_station_id_specified_raises_exception(self):
            transport = Mock(side_effect=[InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client.get_ad_metadata = Mock()

            self.assertRaises(ValueError, client.get_ad_item, '', 'mock_token')

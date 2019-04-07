from unittest import TestCase
from unittest.mock import Mock, call, patch

from pandora import errors
from pandora.models.ad import AdItem
from pandora.models.playlist import AdditionalAudioUrl
from pandora.client import APIClient, BaseAPIClient
from tests.test_pandora.test_models import TestAdItem


class TestAPIClientLogin(TestCase):

    class StubTransport:

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

    def test_login_user_error(self):
        with self.assertRaises(errors.InvalidUserLogin):
            transport = Mock(side_effect=[None, errors.InvalidPartnerLogin])
            client = BaseAPIClient(transport, None, None, None)
            client.login("foobear", "secret")


class TestCallingAPIClient(TestCase):

    def test_call_should_retry_on_token_error(self):
        transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

        client = BaseAPIClient(transport, None, None, None)
        client._authenticate = Mock()

        client.login("foo", "bar")
        client("method")

        client._authenticate.assert_called_with()
        transport.assert_has_calls([call("method"), call("method")])

    def test_playlist_fetches_ads(self):
        fake_playlist = {"items": [
            {"songName": "test"},
            {"adToken": "foo"},
            {"songName": "test"},
        ]}
        with patch.object(APIClient, '__call__', return_value=fake_playlist):
            client = APIClient(Mock(), None, None, None, None)
            client._authenticate = Mock()

            items = client.get_playlist('token_mock')
            self.assertIsInstance(items[1], AdItem)

    def test_ad_support_enabled_parameters(self):
        with patch.object(APIClient, '__call__') as playlist_mock:
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            client.get_playlist('token_mock')

            playlist_mock.assert_has_calls([call("station.getPlaylist",
                                                 additionalAudioUrl='',
                                                 audioAdPodCapable=True,
                                                 includeTrackLength=True,
                                                 stationToken='token_mock',
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

    def test_get_ad_item_(self):
        metamock = patch.object(
            APIClient, '__call__', return_value=TestAdItem.JSON_DATA)

        with metamock as ad_metadata_mock:
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            ad_item = client.get_ad_item('id_mock', 'token_mock')
            assert ad_item.station_id == 'id_mock'
            assert ad_item.ad_token == 'token_mock'

            ad_metadata_mock.assert_has_calls([
                call("ad.getAdMetadata", adToken='token_mock',
                     returnAdTrackingTokens=True, supportAudioAds=True)])

    def test_get_ad_item_with_no_station_id_specified_raises_exception(self):
        transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

        client = APIClient(transport, None, None, None, None)
        client.get_ad_metadata = Mock()

        self.assertRaises(
                errors.ParameterMissing, client.get_ad_item, '', 'token_mock')


class TestCreatingStation(TestCase):

    def test_using_search_token(self):
        client = APIClient(Mock(return_value={}), None, None, None, None)
        client.create_station(search_token="foo")
        client.transport.assert_called_with(
            "station.createStation", musicToken="foo")

    def test_using_artist_token(self):
        client = APIClient(Mock(return_value={}), None, None, None, None)
        client.create_station(artist_token="foo")
        client.transport.assert_called_with(
            "station.createStation", trackToken="foo", musicType="artist")

    def test_using_track_token(self):
        client = APIClient(Mock(return_value={}), None, None, None, None)
        client.create_station(track_token="foo")
        client.transport.assert_called_with(
            "station.createStation", trackToken="foo", musicType="song")

    def test_with_no_token(self):
        with self.assertRaises(KeyError):
            client = APIClient(Mock(), None, None, None, None)
            client.create_station()


class TestCreatingGenreStation(TestCase):

    def test_has_initial_checksum(self):
        fake_data = {
            "categories": [
                {"categoryName": "foo", "stations": []},
            ],

            # Not actually part of the genre station response but is needed to
            # fake out the mock for get_genre_stations_checksum
            "checksum": "foo"
        }
        with patch.object(APIClient, '__call__', return_value=fake_data):
            client = APIClient(Mock(), None, None, None, None)
            station = client.get_genre_stations()
            self.assertEqual(station.checksum, "foo")


class TestAdditionalUrls(TestCase):

    def test_non_iterable_string(self):
        with self.assertRaises(TypeError):
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            client.get_playlist('token_mock', additional_urls='')

    def test_non_iterable_other(self):
        with self.assertRaises(TypeError):
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            client.get_playlist('token_mock',
                                additional_urls=AdditionalAudioUrl.HTTP_32_WMA)

    def test_without_enum(self):
        with patch.object(APIClient, '__call__') as playlist_mock:
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            urls = ['HTTP_128_MP3',
                    'HTTP_24_AACPLUS_ADTS']

            desired = 'HTTP_128_MP3,HTTP_24_AACPLUS_ADTS'

            client.get_playlist('token_mock', additional_urls=urls)

            playlist_mock.assert_has_calls([call("station.getPlaylist",
                                                 additionalAudioUrl=desired,
                                                 audioAdPodCapable=True,
                                                 includeTrackLength=True,
                                                 stationToken='token_mock',
                                                 xplatformAdCapable=True)])


    def test_with_enum(self):
        with patch.object(APIClient, '__call__') as playlist_mock:
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            urls = [AdditionalAudioUrl.HTTP_128_MP3,
                    AdditionalAudioUrl.HTTP_24_AACPLUS_ADTS]

            desired = 'HTTP_128_MP3,HTTP_24_AACPLUS_ADTS'

            client.get_playlist('token_mock', additional_urls=urls)

            playlist_mock.assert_has_calls([call("station.getPlaylist",
                                                 additionalAudioUrl=desired,
                                                 audioAdPodCapable=True,
                                                 includeTrackLength=True,
                                                 stationToken='token_mock',
                                                 xplatformAdCapable=True)])

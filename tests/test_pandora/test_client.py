from unittest import TestCase
from unittest.mock import Mock, call, patch

from pandora import errors
from pandora.models.ad import AdItem
from pandora.models.station import Station
from pandora.models.station import StationList
from pandora.models.search import SearchResult
from pandora.models.bookmark import BookmarkList
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
        fake_playlist = {
            "items": [
                {"songName": "test"},
                {"adToken": "foo"},
                {"songName": "test"},
            ]
        }
        with patch.object(APIClient, "__call__", return_value=fake_playlist):
            client = APIClient(Mock(), None, None, None, None)
            client._authenticate = Mock()

            items = client.get_playlist("token_mock")
            self.assertIsInstance(items[1], AdItem)

    def test_ad_support_enabled_parameters(self):
        with patch.object(APIClient, "__call__") as playlist_mock:
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            client.get_playlist("token_mock")

            playlist_mock.assert_has_calls(
                [
                    call(
                        "station.getPlaylist",
                        additionalAudioUrl="",
                        audioAdPodCapable=True,
                        includeTrackLength=True,
                        stationToken="token_mock",
                        xplatformAdCapable=True,
                    )
                ]
            )


class TestGettingQualities(TestCase):
    def test_with_invalid_quality_returning_all(self):
        result = BaseAPIClient.get_qualities("foo", True)
        self.assertEqual(BaseAPIClient.ALL_QUALITIES, result)

    def test_with_invalid_quality_returning_none(self):
        result = BaseAPIClient.get_qualities("foo", False)
        self.assertEqual([], result)

    def test_with_valid_quality(self):
        result = BaseAPIClient.get_qualities(
            BaseAPIClient.MED_AUDIO_QUALITY, False
        )

        expected = [
            BaseAPIClient.LOW_AUDIO_QUALITY,
            BaseAPIClient.MED_AUDIO_QUALITY,
        ]

        self.assertEqual(expected, result)


class TestGettingAds(TestCase):
    def test_get_ad_item_(self):
        metamock = patch.object(
            APIClient, "__call__", return_value=TestAdItem.JSON_DATA
        )

        with metamock as ad_metadata_mock:
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            ad_item = client.get_ad_item("id_mock", "token_mock")
            assert ad_item.station_id == "id_mock"
            assert ad_item.ad_token == "token_mock"

            ad_metadata_mock.assert_has_calls(
                [
                    call(
                        "ad.getAdMetadata",
                        adToken="token_mock",
                        returnAdTrackingTokens=True,
                        supportAudioAds=True,
                    )
                ]
            )

    def test_get_ad_item_with_no_station_id_specified_raises_exception(self):
        transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

        client = APIClient(transport, None, None, None, None)
        client.get_ad_metadata = Mock()

        self.assertRaises(
            errors.ParameterMissing, client.get_ad_item, "", "token_mock"
        )


class TestCreatingStation(TestCase):
    def test_using_search_token(self):
        client = APIClient(Mock(return_value={}), None, None, None, None)
        client.create_station(search_token="foo")
        client.transport.assert_called_with(
            "station.createStation", musicToken="foo"
        )

    def test_using_artist_token(self):
        client = APIClient(Mock(return_value={}), None, None, None, None)
        client.create_station(artist_token="foo")
        client.transport.assert_called_with(
            "station.createStation", musicToken="foo", musicType="artist"
        )

    def test_using_song_token(self):
        client = APIClient(Mock(return_value={}), None, None, None, None)
        client.create_station(song_token="foo")
        client.transport.assert_called_with(
            "station.createStation", musicToken="foo", musicType="song"
        )

    def test_using_track_token(self):
        client = APIClient(Mock(return_value={}), None, None, None, None)
        client.create_station(track_token="foo")
        client.transport.assert_called_with(
            "station.createStation", trackToken="foo", musicType="song"
        )

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
            "checksum": "foo",
        }
        with patch.object(APIClient, "__call__", return_value=fake_data):
            client = APIClient(Mock(), None, None, None, None)
            station = client.get_genre_stations()
            self.assertEqual(station.checksum, "foo")


class TestAdditionalUrls(TestCase):
    def test_non_iterable_string(self):
        with self.assertRaises(TypeError):
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            client.get_playlist("token_mock", additional_urls="")

    def test_non_iterable_other(self):
        with self.assertRaises(TypeError):
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            client.get_playlist(
                "token_mock", additional_urls=AdditionalAudioUrl.HTTP_32_WMA
            )

    def test_without_enum(self):
        with patch.object(APIClient, "__call__") as playlist_mock:
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            urls = ["HTTP_128_MP3", "HTTP_24_AACPLUS_ADTS"]

            desired = "HTTP_128_MP3,HTTP_24_AACPLUS_ADTS"

            client.get_playlist("token_mock", additional_urls=urls)

            playlist_mock.assert_has_calls(
                [
                    call(
                        "station.getPlaylist",
                        additionalAudioUrl=desired,
                        audioAdPodCapable=True,
                        includeTrackLength=True,
                        stationToken="token_mock",
                        xplatformAdCapable=True,
                    )
                ]
            )

    def test_with_enum(self):
        with patch.object(APIClient, "__call__") as playlist_mock:
            transport = Mock(side_effect=[errors.InvalidAuthToken(), None])

            client = APIClient(transport, None, None, None, None)
            client._authenticate = Mock()

            urls = [
                AdditionalAudioUrl.HTTP_128_MP3,
                AdditionalAudioUrl.HTTP_24_AACPLUS_ADTS,
            ]

            desired = "HTTP_128_MP3,HTTP_24_AACPLUS_ADTS"

            client.get_playlist("token_mock", additional_urls=urls)

            playlist_mock.assert_has_calls(
                [
                    call(
                        "station.getPlaylist",
                        additionalAudioUrl=desired,
                        audioAdPodCapable=True,
                        includeTrackLength=True,
                        stationToken="token_mock",
                        xplatformAdCapable=True,
                    )
                ]
            )


# On the surface this test class seems dumb because it's mostly just exercising
# pass-throughs to the transport but it exists to ensure no subtle errors get
# introduced to API client methods that will only be spotted at runtime (import
# errors, etc...)
class TestAPIClientExhaustive(TestCase):
    def setUp(self):
        self.transport = Mock()
        self.api = APIClient(self.transport, "puser", "ppass", "device")

    def test_register_ad(self):
        self.api.register_ad("sid", "tokens")
        self.transport.assert_called_with(
            "ad.registerAd", stationId="sid", adTrackingTokens="tokens"
        )

    def test_share_music(self):
        self.api.share_music("token", "foo@example.com")
        self.transport.assert_called_with(
            "music.shareMusic", musicToken="token", email="foo@example.com"
        )

    def test_transform_shared_station(self):
        self.api.transform_shared_station("token")
        self.transport.assert_called_with(
            "station.transformSharedStation", stationToken="token"
        )

    def test_share_station(self):
        self.api.share_station("sid", "token", "foo@example.com")
        self.transport.assert_called_with(
            "station.shareStation",
            stationId="sid",
            stationToken="token",
            emails=("foo@example.com",),
        )

    def test_sleep_song(self):
        self.api.sleep_song("token")
        self.transport.assert_called_with("user.sleepSong", trackToken="token")

    def test_set_quick_mix(self):
        self.api.set_quick_mix("id")
        self.transport.assert_called_with(
            "user.setQuickMix", quickMixStationIds=("id",)
        )

    def test_explain_track(self):
        self.api.explain_track("token")
        self.transport.assert_called_with(
            "track.explainTrack", trackToken="token"
        )

    def test_rename_station(self):
        self.api.rename_station("token", "name")
        self.transport.assert_called_with(
            "station.renameStation", stationToken="token", stationName="name"
        )

    def test_delete_station(self):
        self.api.delete_station("token")
        self.transport.assert_called_with(
            "station.deleteStation", stationToken="token"
        )

    def test_delete_music(self):
        self.api.delete_music("seed")
        self.transport.assert_called_with("station.deleteMusic", seedId="seed")

    def test_delete_feedback(self):
        self.api.delete_feedback("id")
        self.transport.assert_called_with(
            "station.deleteFeedback", feedbackId="id"
        )

    def test_add_music(self):
        self.api.add_music("mt", "st")
        self.transport.assert_called_with(
            "station.addMusic", musicToken="mt", stationToken="st"
        )

    def test_add_feedback(self):
        self.api.add_feedback("token", False)
        self.transport.assert_called_with(
            "station.addFeedback", trackToken="token", isPositive=False
        )

    def test_add_artist_bookmark(self):
        self.api.add_artist_bookmark("tt")
        self.transport.assert_called_with(
            "bookmark.addArtistBookmark", trackToken="tt"
        )

    def test_add_song_bookmark(self):
        self.api.add_song_bookmark("tt")
        self.transport.assert_called_with(
            "bookmark.addSongBookmark", trackToken="tt"
        )

    def test_delete_song_bookmark(self):
        self.api.delete_song_bookmark("bt")
        self.transport.assert_called_with(
            "bookmark.deleteSongBookmark", bookmarkToken="bt"
        )

    def test_delete_artist_bookmark(self):
        self.api.delete_artist_bookmark("bt")
        self.transport.assert_called_with(
            "bookmark.deleteArtistBookmark", bookmarkToken="bt"
        )

    def test_get_station_list_checksum(self):
        self.transport.return_value = {"checksum": "foo"}
        self.assertEqual("foo", self.api.get_station_list_checksum())
        self.transport.assert_called_with("user.getStationListChecksum")

    # The following methods use the bare minimum JSON required to construct the
    # models for more detailed model tests look at test_models instead

    def test_get_station_list(self):
        self.transport.return_value = {"stations": []}
        self.assertIsInstance(self.api.get_station_list(), StationList)
        self.transport.assert_called_with(
            "user.getStationList", includeStationArtUrl=True
        )

    def test_get_bookmarks(self):
        self.transport.return_value = {}
        self.assertIsInstance(self.api.get_bookmarks(), BookmarkList)
        self.transport.assert_called_with("user.getBookmarks")

    def test_get_station(self):
        self.transport.return_value = {}
        self.assertIsInstance(self.api.get_station("st"), Station)
        self.transport.assert_called_with(
            "station.getStation",
            stationToken="st",
            includeExtendedAttributes=True,
        )

    def test_search(self):
        self.transport.return_value = {}
        self.assertIsInstance(
            self.api.search(
                "text", include_near_matches=True, include_genre_stations=True
            ),
            SearchResult,
        )
        self.transport.assert_called_with(
            "music.search",
            searchText="text",
            includeNearMatches=True,
            includeGenreStations=True,
        )

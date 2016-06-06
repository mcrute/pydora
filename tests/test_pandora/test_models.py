from unittest import TestCase
from datetime import datetime
from pandora.py2compat import Mock, patch
from pandora import APIClient
from pandora.models.pandora import AdItem, PlaylistModel, SearchResultItem, SearchResult
from pandora.errors import ParameterMissing

import pandora.models as m

class TestField(TestCase):

    def test_defaults(self):
        field = m.Field("name")

        self.assertEqual("name", field.field)
        self.assertIsNone(field.default)
        self.assertIsNone(field.formatter)


class TestModelMetaClass(TestCase):

    class TestModel(m.with_metaclass(m.ModelMetaClass, object)):

        foo = "bar"
        a_field = m.Field("testing")
        __field__ = m.Field("testing")

    def test_metaclass_defines_fields(self):
        self.assertTrue("a_field" in self.TestModel._fields)
        self.assertFalse("foo" in self.TestModel._fields)

    def test_metaclass_ignores_dunder_fields(self):
        self.assertFalse("__field__" in self.TestModel._fields)


class TestPandoraModel(TestCase):

    JSON_DATA = { "field2": ["test2"], "field3": 41 }

    class TestModel(m.PandoraModel):

        THE_LIST = []

        field1 = m.Field("field1", default="a string")
        field2 = m.Field("field2", default=THE_LIST)
        field3 = m.Field("field3", formatter=lambda c, x: x + 1)

    class NoFieldsModel(m.PandoraModel):
        pass

    class ExtraReprModel(m.PandoraModel):

        def __repr__(self):
            return self._base_repr("Foo")

    def test_json_to_date(self):
        expected = datetime(2015, 7, 18, 3, 8, 17)
        result = m.PandoraModel.json_to_date(None, { "time": 1437188897616 })
        # Python2.7 doesn't restore microseconds and we don't care about
        # it anyhow so just remove it for this test
        self.assertEqual(expected, result.replace(microsecond=0))

    def test_init_sets_defaults(self):
        model = self.TestModel(None)
        self.assertEqual(model.field1, "a string")

    def test_init_creates_new_instances_of_mutable_types(self):
        model = self.TestModel(None)
        self.assertEqual(model.field2, [])
        self.assertFalse(model.field2 is self.TestModel.THE_LIST)

    def test_populate_fields(self):
        result = self.TestModel.from_json(None, self.JSON_DATA)
        self.assertEqual("a string", result.field1)
        self.assertEqual(["test2"], result.field2)

    def test_populate_fields_calls_formatter(self):
        result = self.TestModel.from_json(None, self.JSON_DATA)
        self.assertEqual(42, result.field3)

    def test_from_json_list(self):
        json_list = [self.JSON_DATA, self.JSON_DATA]
        result = self.TestModel.from_json_list(None, json_list)
        self.assertEqual(2, len(result))
        self.assertEqual("a string", result[1].field1)

    def test_repr(self):
        expected = "TestModel(field1='a string', field2=['test2'], field3=42)"
        result = self.TestModel.from_json(None, self.JSON_DATA)
        self.assertEqual(expected, repr(result))

    def test_repr_with_extra(self):
        expected = "ExtraReprModel(None, Foo)"
        result = self.ExtraReprModel.from_json(None, self.JSON_DATA)
        self.assertEqual(expected, repr(result))

    def test_repr_with_no_fields(self):
        expected = "NoFieldsModel(None)"
        result = self.NoFieldsModel.from_json(None, self.JSON_DATA)
        self.assertEqual(expected, repr(result))


class TestSubModel(m.PandoraModel):

    idx = m.Field("idx")
    fieldS1 = m.Field("fieldS1")


class TestPandoraListModel(TestCase):

    JSON_DATA = {
            "field1": 42,
            "field2": [
                { "idx": "foo", "fieldS1": "Foo" },
                { "idx": "bar", "fieldS1": "Bar" },
                ]
            }

    class TestModel(m.PandoraListModel):

        __list_key__ = "field2"
        __list_model__ = TestSubModel
        __index_key__ = "idx"

        field1 = m.Field("field1")

    def setUp(self):
        self.result = self.TestModel.from_json(None, self.JSON_DATA)

    def test_creates_sub_models(self):
        self.assertEqual(42, self.result.field1)
        self.assertEqual(2, len(self.result))
        self.assertEqual("Foo", self.result[0].fieldS1)
        self.assertEqual("Bar", self.result[1].fieldS1)

    def test_repr(self):
        expected = ("TestModel(field1=42, [TestSubModel(fieldS1='Foo', "
                    "idx='foo'), TestSubModel(fieldS1='Bar', idx='bar')])")
        self.assertEqual(expected, repr(self.result))

    def test_indexed_model(self):
        self.assertEqual(["bar", "foo"], sorted(self.result.keys()))
        self.assertEqual(self.result._index.items(), self.result.items())

    def test_getting_list_items(self):
        self.assertEqual("Foo", self.result[0].fieldS1)
        self.assertEqual("Bar", self.result[1].fieldS1)

    def test_getting_dictionary_items(self):
        self.assertEqual("Foo", self.result["foo"].fieldS1)
        self.assertEqual("Bar", self.result["bar"].fieldS1)

    def test_getting_keys_vs_indexes_are_identical(self):
        self.assertEqual(self.result["foo"].fieldS1, self.result[0].fieldS1)
        self.assertEqual(self.result["bar"].fieldS1, self.result[1].fieldS1)

    def test_contains(self):
        self.assertTrue("foo" in self.result)
        self.assertTrue(self.result[0] in self.result)


class TestPandoraDictListModel(TestCase):

    JSON_DATA = {
            "field1": 42,
            "fieldD1": [
                { "dictKey": "Foobear",
                  "listKey": [
                      { "idx": "foo", "fieldS1": "Foo" },
                      { "idx": "bar", "fieldS1": "Bar" },
                  ]
                }
            ]
        }

    class TestModel(m.PandoraDictListModel):

        __dict_list_key__ = "fieldD1"
        __list_key__ = "listKey"
        __list_model__ = TestSubModel
        __dict_key__ = "dictKey"

        field1 = m.Field("field1")

    def setUp(self):
        self.result = self.TestModel.from_json(None, self.JSON_DATA)

    def test_creates_sub_models(self):
        self.assertEqual(42, self.result.field1)

        self.assertEqual("Foo", self.result["Foobear"][0].fieldS1)
        self.assertEqual("foo", self.result["Foobear"][0].idx)

        self.assertEqual("Bar", self.result["Foobear"][1].fieldS1)
        self.assertEqual("bar", self.result["Foobear"][1].idx)

    def test_repr(self):
        expected = ("TestModel(field1=42, {'Foobear': "
                    "[TestSubModel(fieldS1='Foo', idx='foo'), "
                    "TestSubModel(fieldS1='Bar', idx='bar')]})")
        self.assertEqual(expected, repr(self.result))


class TestAdItem(TestCase):

    JSON_DATA = {
        'audioUrlMap': {
            'mediumQuality': {
                'audioUrl': 'med_url_mock', 'bitrate': '64', 'protocol': 'http', 'encoding': 'aacplus'
            },
            'highQuality': {
                'audioUrl': 'high_url_mock', 'bitrate': '64', 'protocol': 'http', 'encoding': 'aacplus'
            },
            'lowQuality': {
                'audioUrl': 'low_url_mock', 'bitrate': '32', 'protocol': 'http', 'encoding': 'aacplus'}},
            'clickThroughUrl': 'click_url_mock',
            'imageUrl': 'img_url_mock',
            'companyName': '',
            'title': '',
            'trackGain': '0.0',
            'adTrackingTokens': ['token_1_mock', 'token_2_mock']
    }

    def setUp(self):
        api_client_mock = Mock(spec=APIClient)
        api_client_mock.default_audio_quality = APIClient.HIGH_AUDIO_QUALITY
        self.result = AdItem.from_json(api_client_mock, self.JSON_DATA)
        self.result.station_id = 'station_id_mock'
        self.result.ad_token = 'token_mock'

    def test_is_ad_is_true(self):
        assert self.result.is_ad is True

    def test_register_ad(self):
        self.result._api_client.register_ad = Mock()
        self.result.register_ad('id_mock')

        assert self.result._api_client.register_ad.called

    def test_register_ad_raises_exception_if_no_tracking_tokens_available(self):
        with self.assertRaises(ParameterMissing):
            self.result.tracking_tokens = []
            self.result._api_client.register_ad = Mock(spec=AdItem)

            self.result.register_ad('id_mock')

            assert self.result._api_client.register_ad.called

    def test_prepare_playback(self):
        with patch.object(PlaylistModel, 'prepare_playback') as super_mock:

            self.result.register_ad = Mock()
            self.result.prepare_playback()
            assert self.result.register_ad.called
            assert super_mock.called

    def test_prepare_playback_raises_paramater_missing(self):
        with patch.object(PlaylistModel, 'prepare_playback') as super_mock:

            self.result.register_ad = Mock(side_effect=ParameterMissing('No ad tracking tokens provided for '
                                                                        'registration.')
                                           )
            self.assertRaises(ParameterMissing, self.result.prepare_playback)
            assert self.result.register_ad.called
            assert not super_mock.called

    def test_prepare_playback_handles_paramater_missing_if_no_tokens(self):
        with patch.object(PlaylistModel, 'prepare_playback') as super_mock:

            self.result.tracking_tokens = []
            self.result.register_ad = Mock(side_effect=ParameterMissing('No ad tracking tokens provided for '
                                                                        'registration.'))
            self.result.prepare_playback()
            assert self.result.register_ad.called
            assert super_mock.called


class TestSearchResultItem(TestCase):

    SONG_JSON_DATA = {
        "artistName": "artist_name_mock",
        "musicToken": "S0000000",
        "songName": "song_name_mock",
        "score": 100
    }

    ARTIST_JSON_DATA = {
        "artistName": "artist_name_mock",
        "musicToken": "R0000000",
        "likelyMatch": False,
        "score": 100
    }

    COMPOSER_JSON_DATA = {
        "artistName": "composer_name_mock",
        "musicToken": "C0000000",
        "likelyMatch": False,
        "score": 100
    }

    GENRE_JSON_DATA = {
        "stationName": "station_name_mock",
        "musicToken": "G0000000",
        "score": 100
    }

    def setUp(self):
        self.api_client_mock = Mock(spec=APIClient)
        self.api_client_mock.default_audio_quality = APIClient.HIGH_AUDIO_QUALITY

    def test_is_song(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.SONG_JSON_DATA)
        assert result.is_song
        assert not result.is_artist
        assert not result.is_composer
        assert not result.is_genre_station

    def test_is_artist(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.ARTIST_JSON_DATA)
        assert not result.is_song
        assert result.is_artist
        assert not result.is_composer
        assert not result.is_genre_station

    def test_is_composer(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.COMPOSER_JSON_DATA)
        assert not result.is_song
        assert not result.is_artist
        assert result.is_composer
        assert not result.is_genre_station

    def test_is_genre_station(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.GENRE_JSON_DATA)
        assert not result.is_song
        assert not result.is_artist
        assert not result.is_composer
        assert result.is_genre_station

    def test_create_station(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.SONG_JSON_DATA)

        self.assertRaises(NotImplementedError, result.create_station())


class TestArtistSearchResultItem(TestCase):

    ARTIST_JSON_DATA = {
        "artistName": "artist_name_mock",
        "musicToken": "R0000000",
        "likelyMatch": False,
        "score": 100
    }

    COMPOSER_JSON_DATA = {
        "artistName": "composer_name_mock",
        "musicToken": "C0000000",
        "likelyMatch": False,
        "score": 100
    }

    def setUp(self):
        self.api_client_mock = Mock(spec=APIClient)
        self.api_client_mock.default_audio_quality = APIClient.HIGH_AUDIO_QUALITY

    def test_repr(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.ARTIST_JSON_DATA)
        expected = ("ArtistSearchResultItem(artist='artist_name_mock', likely_match=False, score=100, token='R0000000')")
        self.assertEqual(expected, repr(result))

        result = SearchResultItem.from_json(self.api_client_mock, self.COMPOSER_JSON_DATA)
        expected = ("ArtistSearchResultItem(artist='composer_name_mock', likely_match=False, score=100, token='C0000000')")
        self.assertEqual(expected, repr(result))

    def test_create_station(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.ARTIST_JSON_DATA)
        result._api_client.create_station = Mock()

        result.create_station()
        result._api_client.create_station.assert_called_with(artist_token=result.token)


class TestSongSearchResultItem(TestCase):

    SONG_JSON_DATA = {
        "artistName": "artist_name_mock",
        "musicToken": "S0000000",
        "songName": "song_name_mock",
        "score": 100
    }

    def setUp(self):
        self.api_client_mock = Mock(spec=APIClient)
        self.api_client_mock.default_audio_quality = APIClient.HIGH_AUDIO_QUALITY

    def test_repr(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.SONG_JSON_DATA)
        expected = ("SongSearchResultItem(artist='artist_name_mock', score=100, song_name='song_name_mock', token='S0000000')")
        self.assertEqual(expected, repr(result))

    def test_create_station(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.SONG_JSON_DATA)
        result._api_client.create_station = Mock()

        result.create_station()
        result._api_client.create_station.assert_called_with(track_token=result.token)


class TestGenreStationSearchResultItem(TestCase):

    GENRE_JSON_DATA = {
        "stationName": "station_name_mock",
        "musicToken": "G0000000",
        "score": 100
    }

    def setUp(self):
        self.api_client_mock = Mock(spec=APIClient)
        self.api_client_mock.default_audio_quality = APIClient.HIGH_AUDIO_QUALITY

    def test_repr(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.GENRE_JSON_DATA)
        expected = ("GenreStationSearchResultItem(score=100, station_name='station_name_mock', token='G0000000')")
        self.assertEqual(expected, repr(result))

    def test_create_station(self):
        result = SearchResultItem.from_json(self.api_client_mock, self.GENRE_JSON_DATA)
        result._api_client.create_station = Mock()

        result.create_station()
        result._api_client.create_station.assert_called_with(search_token=result.token)


class TestSearchResult(TestCase):

    JSON_DATA = {
        'nearMatchesAvailable': True,
        'explanation': '',
        'songs': [{
            'artistName': 'song_artist_mock',
            'musicToken': 'S0000000',
            'songName': 'song_name_mock',
            'score': 100
        }],
        'artists': [{
            'artistName': 'artist_mock',
            'musicToken': 'R000000',
            'likelyMatch': False,
            'score': 80
        }],
        'genreStations': [{
            'musicToken': 'G0000',
            'stationName': 'station_mock',
            'score': 50
        }]
    }

    def setUp(self):
        api_client_mock = Mock(spec=APIClient)
        api_client_mock.default_audio_quality = APIClient.HIGH_AUDIO_QUALITY
        self.result = SearchResult.from_json(api_client_mock, self.JSON_DATA)

    def test_repr(self):
        expected = ("SearchResult(artists=[ArtistSearchResultItem(artist='artist_mock', likely_match=False, score=80, "
                    "token='R000000')], explanation='', genre_stations=[GenreStationSearchResultItem(score=50, "
                    "station_name='station_mock', token='G0000')], nearest_matches_available=True, "
                    "songs=[SongSearchResultItem(artist='song_artist_mock', score=100, song_name='song_name_mock', "
                    "token='S0000000')])")
        self.assertEqual(expected, repr(self.result))

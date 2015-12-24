from unittest import TestCase
from datetime import datetime
from pandora.py2compat import Mock, patch
from pandora import APIClient
from pandora.models.pandora import AdItem, PlaylistModel

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

    def setUp(self):
        api_client_mock = Mock(spec=APIClient)
        api_client_mock.default_audio_quality = APIClient.HIGH_AUDIO_QUALITY
        self.result = AdItem.from_json(api_client_mock, self.JSON_DATA)

    def test_is_ad_is_true(self):
        assert self.result.is_ad is True

    def test_register_ad(self):
        self.result._api_client.register_ad = Mock()
        self.result.register_ad('id_dummy')

        assert self.result._api_client.register_ad.called

    def test_prepare_playback(self):
        with patch.object(PlaylistModel, 'prepare_playback') as super_mock:

            self.result.register_ad = Mock()
            self.result.prepare_playback()
            assert self.result.register_ad.called
            assert super_mock.called

from unittest import TestCase
from datetime import datetime

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

    fieldS1 = m.Field("fieldS1")


class TestPandoraListModel(TestCase):

    JSON_DATA = {
            "field1": 42,
            "field2": [{"fieldS1": "Foo" }, { "fieldS1": "Bar" }]
            }

    class TestModel(m.PandoraListModel):

        __list_key__ = "field2"
        __list_model__ = TestSubModel

        field1 = m.Field("field1")

    def test_creates_sub_models(self):
        result = self.TestModel.from_json(None, self.JSON_DATA)
        self.assertEqual(42, result.field1)
        self.assertEqual(2, len(result))
        self.assertEqual("Foo", result[0].fieldS1)
        self.assertEqual("Bar", result[1].fieldS1)

    def test_repr(self):
        expected = ("TestModel(field1=42, [TestSubModel(fieldS1='Foo'), "
                    "TestSubModel(fieldS1='Bar')])")
        result = self.TestModel.from_json(None, self.JSON_DATA)
        self.assertEqual(expected, repr(result))

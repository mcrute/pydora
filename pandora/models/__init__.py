from datetime import datetime
from collections import namedtuple


def with_metaclass(meta, *bases):
    return meta("NewBase", bases, {})


class Field(namedtuple("Field", ["field", "default", "formatter"])):

    def __new__(cls, field, default=None, formatter=None):
        return super(Field, cls).__new__(cls, field, default, formatter)


class SyntheticField(namedtuple("SyntheticField", ["field"])):
    """Field That Requires Synthesis

    Synthetic fields may exist in the data but generally do not and require
    additional synthesis to arrive ate a sane value. Subclasses must define
    a formatter method that receives an API client, field name, and full data
    payload.
    """

    default = None

    @staticmethod
    def formatter(api_client, field, data):  # pragma: no cover
        raise NotImplementedError


class ModelMetaClass(type):

    def __new__(cls, name, parents, dct):
        dct["_fields"] = fields = {}
        new_dct = dct.copy()

        for key, val in dct.items():
            if key.startswith("__"):
                continue

            if isinstance(val, Field) or isinstance(val, SyntheticField):
                fields[key] = val
                del new_dct[key]

        return super(ModelMetaClass, cls).__new__(cls, name, parents, new_dct)


class PandoraModel(with_metaclass(ModelMetaClass, object)):

    @staticmethod
    def json_to_date(api_client, data):
        return datetime.utcfromtimestamp(data["time"] / 1000)

    @classmethod
    def from_json_list(cls, api_client, data):
        return [cls.from_json(api_client, item) for item in data]

    def __init__(self, api_client):
        self._api_client = api_client

        safe_types = (type(None), str, bytes, int, bool)

        for key, value in self._fields.items():
            default = value.default

            if not isinstance(default, safe_types):
                default = type(default)()

            setattr(self, key, default)

    @staticmethod
    def populate_fields(api_client, instance, data):
        for key, value in instance.__class__._fields.items():
            newval = data.get(value.field, value.default)

            if isinstance(value, SyntheticField):
                newval = value.formatter(api_client, value.field, data, newval)
                setattr(instance, key, newval)
                continue

            if newval and value.formatter:
                newval = value.formatter(api_client, newval)

            setattr(instance, key, newval)

    @classmethod
    def from_json(cls, api_client, data):
        self = cls(api_client)
        PandoraModel.populate_fields(api_client, self, data)
        return self

    def _base_repr(self, and_also=None):
        items = [
            "=".join((key, repr(getattr(self, key))))
            for key in sorted(self._fields.keys())]

        if items:
            output = ", ".join(items)
        else:
            output = None

        if and_also:
            return "{}({}, {})".format(self.__class__.__name__,
                                       output, and_also)
        else:
            return "{}({})".format(self.__class__.__name__, output)

    def __repr__(self):
        return self._base_repr()


class PandoraListModel(PandoraModel, list):

    __list_key__ = None
    __list_model__ = None
    __index_key__ = None

    def __init__(self, *args, **kwargs):
        super(PandoraListModel, self).__init__(*args, **kwargs)
        self._index = {}

    @classmethod
    def from_json(cls, api_client, data):
        self = cls(api_client)
        PandoraModel.populate_fields(api_client, self, data)

        for item in data[cls.__list_key__]:
            model = cls.__list_model__.from_json(api_client, item)

            if self.__index_key__:
                value = getattr(model, self.__index_key__)
                self._index[value] = model

            self.append(model)

        return self

    def __getitem__(self, key):
        item = self._index.get(key, None)
        if item:
            return item
        else:
            return list.__getitem__(self, key)

    def __contains__(self, key):
        if key in self._index:
            return True
        else:
            return list.__contains__(self, key)

    def keys(self):
        return self._index.keys()

    def items(self):
        return self._index.items()

    def __repr__(self):
        return self._base_repr(and_also=list.__repr__(self))


class PandoraDictListModel(PandoraModel, dict):

    __dict_list_key__ = None
    __dict_key__ = None
    __list_key__ = None
    __list_model__ = None

    @classmethod
    def from_json(cls, api_client, data):
        self = cls(api_client)
        PandoraModel.populate_fields(api_client, self, data)

        for item in data[self.__dict_list_key__]:
            key = item[self.__dict_key__]
            self[key] = []

            for part in item[self.__list_key__]:
                self[key].append(
                    cls.__list_model__.from_json(api_client, part))

        return self

    def __repr__(self):
        return self._base_repr(and_also=dict.__repr__(self))

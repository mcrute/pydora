from datetime import datetime
from collections import namedtuple


def with_metaclass(meta, *bases):
    return meta("NewBase", bases, {})


class Field(namedtuple("Field", ["field", "default", "formatter"])):

    def __new__(cls, field, default=None, formatter=None):
        return super(Field, cls).__new__(cls, field, default, formatter)


class ModelMetaClass(type):

    def __new__(cls, name, parents, dct):
        dct["_fields"] = fields = {}
        new_dct = dct.copy()

        for key, val in dct.items():
            if isinstance(val, Field):
                fields[key] = val
                del new_dct[key]

        return super(ModelMetaClass, cls).__new__(cls, name, parents, new_dct)


class PandoraModel(with_metaclass(ModelMetaClass, object)):

    @staticmethod
    def json_to_date(api_client, data):
        return datetime.utcfromtimestamp(data["time"] / 1000)

    def __init__(self, api_client):
        self._api_client = api_client

        try:
            safe_types = (type(None), basestring, int, bool)
        except NameError:
            safe_types = (type(None), str, bytes, int, bool)

        for key, value in self._fields.items():
            default = value.default

            if not isinstance(default, safe_types):
                default = type(default)()

            setattr(self, key, default)

    @staticmethod
    def populate_fields(api_client, instance, data):
        for key, value in instance.__class__._fields.items():
            if key.startswith("__"):
                continue

            newval = data.get(value.field, value.default)

            if newval and value.formatter:
                newval = value.formatter(api_client, newval)

            setattr(instance, key, newval)

    @classmethod
    def from_json(cls, api_client, data):
        self = cls(api_client)
        PandoraModel.populate_fields(api_client, self, data)
        return self

    @classmethod
    def from_json_list(cls, api_client, data):
        return [cls.from_json(api_client, item) for item in data]

    def __repr__(self):
        output = ", ".join([
            "=".join((key, repr(getattr(self, key))))
            for key in self._fields.keys()])

        return "{}({})".format(self.__class__.__name__, output)


class PandoraListModel(PandoraModel, list):

    __list_key__ = None
    __list_model__ = None

    @classmethod
    def from_json(cls, api_client, data):
        self = cls(api_client)
        PandoraModel.populate_fields(api_client, self, data)

        for station in data[cls.__list_key__]:
            self.append(cls.__list_model__.from_json(api_client, station))

        return self

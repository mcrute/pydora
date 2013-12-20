from datetime import datetime
from collections import namedtuple


class Field(namedtuple('Field', ['field', 'default', 'formatter'])):

    def __new__(cls, field, default=None, formatter=None):
        return super(Field, cls).__new__(cls, field, default, formatter)


class ModelMetaClass(type):

    def __new__(cls, name, parents, dct):
        dct['_fields'] = fields = {}

        for key, val in dct.items():
            if isinstance(val, Field):
                fields[key] = val
                del dct[key]

        return super(ModelMetaClass, cls).__new__(cls, name, parents, dct)


class PandoraModel(object):

    __metaclass__ = ModelMetaClass

    @staticmethod
    def json_to_date(data):
        return datetime.utcfromtimestamp(data["time"] / 1000)

    def __init__(self, api_client):
        self._api_client = api_client
        safe_types = (type(None), basestring, int, bool)

        for key, value in self._fields.items():
            default = value.default

            if not isinstance(default, safe_types):
                default = type(default)()

            setattr(self, key, default)

    @classmethod
    def from_json(cls, api_client, data):
        self = cls(api_client)

        for key, value in cls._fields.items():
            newval = data.get(value.field, value.default)

            if newval and value.formatter:
                newval = value.formatter(newval)

            setattr(self, key, newval)

        return self

    def __str__(self):
        return "{}({!r}, {!r})".format(self.__class__.__name__, self.id,
                self.name)

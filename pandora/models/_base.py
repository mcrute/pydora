from datetime import datetime
from collections import namedtuple


class Field(namedtuple("Field", ["field", "default", "formatter", "model"])):
    """Model Field

    Model fields represent JSON key/value pairs. When added to a PandoraModel
    the describe the unpacking logic for the API JSON and will be replaced at
    runtime with the values from the parsed JSON or their defaults.

    field
        name of the field from the incoming JSON
    default
        default value if key does not exist in the incoming JSON, None if not
        provided
    formatter
        formatter function accepting an API client and the value of the field
        as arguments, will be called on the value of the data for the field key
        in the incoming JSON. The return value of this function is used as the
        value of the field on the model object.
    model
        the model class that the value of this field should be constructed into
        the model construction logic will handle building a list or single
        model based on the type of data in the JSON
    """

    def __new__(cls, field, default=None, formatter=None, model=None):
        return super().__new__(cls, field, default, formatter, model)


class SyntheticField(namedtuple("SyntheticField", ["field"])):
    """Field Requiring Synthesis

    Synthetic fields may exist in the data but generally do not and require
    additional synthesis to arrive ate a sane value. Subclasses must define
    a formatter method that receives an API client, field name, and full data
    payload.
    """

    def formatter(self, api_client, data, newval):
        """Format Value for Model

        The return value of this method is used as a value for the field in the
        model of which this field is a member

        api_client
            instance of a Pandora API client
        data
            complete JSON data blob for the parent model of which this field is
            a member
        newval
            the value of this field as retrieved from the JSON data after
            having resolved default value logic
        """
        raise NotImplementedError


class DateField(SyntheticField):
    """Date Field

    Handles a JSON map that contains a time field which is the timestamp with
    nanosecond precision.
    """

    def formatter(self, api_client, data, newval):
        if not newval:
            return None

        return datetime.utcfromtimestamp(newval["time"] / 1000)


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

        return super().__new__(cls, name, parents, new_dct)


class PandoraModel(metaclass=ModelMetaClass):
    """Pandora API Model

    A single object representing a Pandora data object. Subclasses are
    specified declaratively and contain Field objects as well as optionally
    other methods. The end result object after loading from JSON will be a
    normal python object with all fields declared in the schema populated and
    consumers of these instances can ignore all of the details of this class.
    """

    @classmethod
    def from_json_list(cls, api_client, data):
        """Convert a list of JSON values to a list of models"""
        return [cls.from_json(api_client, item) for item in data]

    def __init__(self, api_client):
        self._api_client = api_client

        safe_types = (type(None), str, bytes, int, bool)

        for key, value in self._fields.items():
            default = getattr(value, "default", None)

            if not isinstance(default, safe_types):
                default = type(default)()

            setattr(self, key, default)

    @staticmethod
    def populate_fields(api_client, instance, data):
        """Populate all fields of a model with data

        Given a model with a PandoraModel superclass will enumerate all
        declared fields on that model and populate the values of their Field
        and SyntheticField classes. All declared fields will have a value after
        this function runs even if they are missing from the incoming JSON.
        """
        for key, value in instance.__class__._fields.items():
            default = getattr(value, "default", None)
            newval = data.get(value.field, default)

            if isinstance(value, SyntheticField):
                newval = value.formatter(api_client, data, newval)
                setattr(instance, key, newval)
                continue

            model_class = getattr(value, "model", None)
            if newval and model_class:
                if isinstance(newval, list):
                    newval = model_class.from_json_list(api_client, newval)
                else:
                    newval = model_class.from_json(api_client, newval)

            if newval and value.formatter:
                newval = value.formatter(api_client, newval)

            setattr(instance, key, newval)

    @classmethod
    def from_json(cls, api_client, data):
        """Convert one JSON value to a model object"""
        self = cls(api_client)
        PandoraModel.populate_fields(api_client, self, data)
        return self

    def _base_repr(self, and_also=None):
        """Common repr logic for subclasses to hook"""
        items = [
            "=".join((key, repr(getattr(self, key))))
            for key in sorted(self._fields.keys())
        ]

        if items:
            output = ", ".join(items)
        else:
            output = None

        if and_also:
            return "{}({}, {})".format(
                self.__class__.__name__, output, and_also
            )
        else:
            return "{}({})".format(self.__class__.__name__, output)

    def __repr__(self):
        return self._base_repr()


class PandoraListModel(PandoraModel, list):
    """Dict-like List of Pandora Models

    Processes a JSON map, expecting a key that contains a list of maps. Will
    process each item in the list, creating models for each one and a secondary
    index based on the value in each item. This object behaves like a list and
    like a dict.

    Example JSON:

        {
            "__list_key__": [
                { "__index_key__": "key", "other": "fields" },
                { "__index_key__": "key", "other": "fields" }
            ],
            "other": "fields"
        }

    __list_key__
        they key within the parent map containing a list
    __list_model__
        model class to use when constructing models for list contents
    __index_key__
        key from each object in the model list that will be used as an index
        within this object
    """

    __list_key__ = None
    __list_model__ = None
    __index_key__ = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
    """Dict of Models

    Processes a JSON map, expecting a key that contains a list of maps, each of
    which contain a key and a list of values which are the final models. Will
    process each item in the list, creating models for each one and storing the
    constructed models in a map indexed by the dict key. Duplicated sub-maps
    will be merged into one key for this model.

    Example JSON:

        {
            "__dict_list_key__": [
                {
                    "__dict_key__": "key for this model",
                    "__list_key__": [
                        { "model": "fields" },
                        { "model": "fields" }
                    ]
                }
            ],
            "other": "fields"
        }

    __dict_list_key__
        the key within the parent map that contains the maps that contain
        lists of models
    __dict_key__
        the key within the nested map that contains the key for this object
    __list_key__
        they key within the nested map that contains the list of models
    __list_model__
        model class to use when constructing models for list contents
    """

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
                    cls.__list_model__.from_json(api_client, part)
                )

        return self

    def __repr__(self):
        return self._base_repr(and_also=dict.__repr__(self))

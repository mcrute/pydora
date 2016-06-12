"""
Pandora API Client Builders

This module provides a set of builder classes that can turn various
configuration formats into a fully built APIClient.
"""
import os.path

from .py2compat import ConfigParser
from . import Encryptor, APITransport, DEFAULT_API_HOST, APIClient


class TranslatingDict(dict):
    """Abstract Key/Value Translating Dictionary

    Dictionary that translates keys using a static map of old key to new key
    and values using a map of key to value translating function. The value
    translating function will be called with the key and value read and is
    expected to return a translated value for storage. Keys and values not
    matched for translation are stored as provided.

    This otherwise behaves as a standard dictionary.

    Subclasses must provide KEY_TRANSLATIONS and VALUE_TRANSLATIONS even if
    they are just empty dictionaries.
    """

    KEY_TRANSLATIONS = None
    VALUE_TRANSLATIONS = None

    def __init__(self, initial=None):
        super(TranslatingDict, self).__init__()

        assert self.KEY_TRANSLATIONS is not None
        assert self.VALUE_TRANSLATIONS is not None

        if not initial:
            return

        if hasattr(initial, "items"):
            values = initial.items()
        else:
            values = initial

        for key, value in values:
            self.put(key, value)

    def was_translated(self, from_key, to_key):
        pass

    def translate_key(self, key):
        key = key.strip().upper()
        to_key = self.KEY_TRANSLATIONS.get(key, None)

        if to_key:
            self.was_translated(key, to_key)
            return to_key
        else:
            return key

    def translate_value(self, key, value):
        if hasattr(value, "strip"):
            value = value.strip()

        return self.VALUE_TRANSLATIONS.get(key, lambda v: v)(value)

    def put(self, key, value):
        self[key] = value

    def __setitem__(self, key, value):
        key = self.translate_key(key)
        super(TranslatingDict, self).__setitem__(
            key, self.translate_value(key, value))


class APIClientBuilder(object):
    """Abstract API Client Builder

    Provides the basic functions for building an API client. Expects a
    dictionary of standard configuration options.

    Required values:
    * DECRYPTION_KEY - Pandora API decryption key
    * ENCRYPTION_KEY - Pandora API encryption key
    * PARTNER_USER - Pandora API partner username
    * PARTNER_PASSWORD - Pandora API partner password
    * DEVICE - Pandora API device type identifier

    Optional values:
    * API_HOST - API hostname and path to API
    * PROXY - HTTP/HTTPS proxy hostname
    * AUDIO_QUALITY - A supported audio quality (see APIClient)
    """

    DEFAULT_CLIENT_CLASS = APIClient

    def __init__(self, client_class=None):
        self.client_class = client_class or self.DEFAULT_CLIENT_CLASS

    def build_from_settings_dict(self, settings):
        enc = Encryptor(settings["DECRYPTION_KEY"],
                        settings["ENCRYPTION_KEY"])

        trans = APITransport(enc,
                             settings.get("API_HOST", DEFAULT_API_HOST),
                             settings.get("PROXY", None))

        quality = settings.get("AUDIO_QUALITY",
                               self.client_class.MED_AUDIO_QUALITY)

        return self.client_class(trans, settings["PARTNER_USER"],
                                 settings["PARTNER_PASSWORD"],
                                 settings["DEVICE"], quality)


class SettingsDict(TranslatingDict):
    """Settings Translating Dictionary

    Maps old setting keys to new ones. Should be removed when ready to break
    backwards compatibility.
    """

    KEY_TRANSLATIONS = {
        "USERNAME": "PARTNER_USER",
        "PASSWORD": "PARTNER_PASSWORD",
        "DEFAULT_AUDIO_QUALITY": "AUDIO_QUALITY",
    }

    VALUE_TRANSLATIONS = {}

    def was_translated(self, from_key, to_key):
        pass


class SettingsDictBuilder(APIClientBuilder):
    """Settings Dictionary Client Builder

    Builds an API client based on a translated settings dictionary.
    """

    def __init__(self, settings, **kwargs):
        self.settings = settings
        super(SettingsDictBuilder, self).__init__(**kwargs)

    def build(self):
        settings = SettingsDict(self.settings)
        return self.build_from_settings_dict(settings)


class FileBasedClientBuilder(APIClientBuilder):
    """Abstract File Based Client Builder

    Provides base functionality for client builders that load their settings
    from files.
    """

    DEFAULT_CONFIG_FILE = ""

    def __init__(self, path=None, authenticate=True, **kwargs):
        self.path = path or self.DEFAULT_CONFIG_FILE
        self.authenticate = authenticate
        super(FileBasedClientBuilder, self).__init__(**kwargs)

    @property
    def file_exists(self):
        return os.path.exists(self._path)

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = os.path.expanduser(path)

    def parse_config(self):
        raise NotImplementedError

    def build(self):
        if not self.file_exists:
            raise IOError("File not found: {}".format(self.path))

        config = self.parse_config()
        client = self.build_from_settings_dict(config)

        if self.authenticate:
            client.login(config["USER"]["USERNAME"],
                         config["USER"]["PASSWORD"])

        return client


class PydoraConfigFileBuilder(FileBasedClientBuilder):
    """Pydora Config Format Client Builder

    Builds API client for original pydora configuration format.
    """

    DEFAULT_CONFIG_FILE = "~/.pydora.cfg"

    @staticmethod
    def cfg_to_dict(cfg, key, kind=SettingsDict):
        return kind((k.strip().upper(), v.strip())
                    for k, v in cfg.items(key, raw=True))

    def parse_config(self):
        cfg = ConfigParser()

        with open(self.path) as file:
            cfg.read_file(file)

        settings = PydoraConfigFileBuilder.cfg_to_dict(cfg, "api")
        settings["user"] = PydoraConfigFileBuilder.cfg_to_dict(
            cfg, "user", dict)

        return settings


class PianobarSettingsDict(TranslatingDict):
    """Pianobar Translating Dictionary
    """

    KEY_TRANSLATIONS = {
        "DECRYPT_PASSWORD": "DECRYPTION_KEY",
        "ENCRYPT_PASSWORD": "ENCRYPTION_KEY",
        "RPC_HOST": "API_HOST",
        "CONTROL_PROXY": "PROXY",
    }

    VALUE_TRANSLATIONS = {
        "API_HOST": lambda v: "{}/services/json/".format(v),
        "AUDIO_QUALITY": lambda v: "{}Quality".format(v),
    }


class PianobarConfigFileBuilder(FileBasedClientBuilder):
    """Pianobar Config File Client Builder

    Builds an API client from a Pianobar config file.
    """

    DEFAULT_CONFIG_FILE = "~/.config/pianobar/config"

    def parse_config(self):
        settings = PianobarSettingsDict()

        with open(self.path, "r") as file:
            for line in file.readlines():
                line = line.strip()

                if line and not line.startswith("#"):
                    settings.put(*line.split("=", 1))

        settings["USER"] = {
            "USERNAME": settings.pop("USER"),
            "PASSWORD": settings.pop("PASSWORD"),
        }

        return settings

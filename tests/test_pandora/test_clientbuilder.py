import os
from unittest import TestCase

import pandora.clientbuilder as cb
from pandora.py2compat import Mock
from pandora import APIClient, DEFAULT_API_HOST


class TestTranslatingDict(TestCase):

    class TestDict(cb.TranslatingDict):

        KEY_TRANSLATIONS = { "FOO": "BAR" }
        VALUE_TRANSLATIONS = { "BAZ": lambda v: v + 1 }
        callback_value = None

        def was_translated(self, from_key, to_key):
            self.callback_value = (from_key, to_key)

    def setUp(self):
        self.dct = self.TestDict()

    def test_construction_with_dict(self):
        dct = self.TestDict({ "BIZ": 1, "BUZ": 2 })

        self.assertEqual(1, dct["BIZ"])
        self.assertEqual(2, dct["BUZ"])

    def test_construction_with_list(self):
        dct = self.TestDict([("key", "value")])

        self.assertEqual("value", dct["KEY"])

    def test_key_translation(self):
        self.dct.put(" TEST ", "value")
        self.dct.put("MoRe", 1)
        self.dct.put("foo", True)

        self.assertEqual("value", self.dct["TEST"])
        self.assertEqual(1, self.dct["MORE"])
        self.assertEqual(True, self.dct["BAR"])

    def test_value_translation(self):
        dct = self.TestDict({ " Baz": 41 })

        self.assertEqual(42, dct["BAZ"])

    def test_setitem(self):
        self.dct["Foo"] = "bar"

        self.assertEqual("bar", self.dct["BAR"])

    def test_put(self):
        self.dct.put("Foo", "bar")

        self.assertEqual("bar", self.dct["BAR"])

    def test_key_translation_hook(self):
        self.dct.put("Foo", "bar")
        self.assertEqual(("FOO", "BAR"), self.dct.callback_value)


class TestSettingsDictBuilder(TestCase):

    def _build_minimal(self):
        return cb.SettingsDictBuilder({
            "DECRYPTION_KEY": "dec",
            "ENCRYPTION_KEY": "enc",
            "PARTNER_USER": "user",
            "PARTNER_PASSWORD": "pass",
            "DEVICE": "dev",
        }).build()

    def _build_maximal(self):
        return cb.SettingsDictBuilder({
            "DECRYPTION_KEY": "dec",
            "ENCRYPTION_KEY": "enc",
            "PARTNER_USER": "user",
            "PARTNER_PASSWORD": "pass",
            "DEVICE": "dev",
            "PROXY": "proxy.example.com",
            "AUDIO_QUALITY": "high",
            "AD_SUPPORT_ENABLED": True,
            "API_HOST": "example.com",
        }).build()

    def test_building(self):
        client = self._build_minimal()

        self.assertTrue(isinstance(client, APIClient))

    def test_default_values(self):
        client = self._build_minimal()

        self.assertEqual({}, client.transport._http.proxies)
        self.assertEqual(DEFAULT_API_HOST, client.transport.api_host)
        self.assertEqual(APIClient.MED_AUDIO_QUALITY,
                client.default_audio_quality)
        self.assertEqual(True,
                client.ad_support_enabled)

    def test_validate_client(self):
        client = self._build_maximal()
        expected_proxies = {
                "http": "proxy.example.com",
                "https": "proxy.example.com"
                }

        self.assertIsNotNone(client.transport.cryptor.bf_in)
        self.assertIsNotNone(client.transport.cryptor.bf_out)

        self.assertEqual("user", client.partner_user)
        self.assertEqual("pass", client.partner_password)
        self.assertEqual("dev", client.device)

        self.assertEqual(expected_proxies, client.transport._http.proxies)
        self.assertEqual("example.com", client.transport.api_host)
        self.assertEqual("high", client.default_audio_quality)
        self.assertEqual(True, client.ad_support_enabled)


class TestFileBasedBuilder(TestCase):

    class StubBuilder(cb.FileBasedClientBuilder):

        DEFAULT_CONFIG_FILE = "foo"

        def parse_config(self):
            return { "USER": { "USERNAME": "U", "PASSWORD": "P" }}

        def build_from_settings_dict(self, config):
            mock = Mock()
            mock.login = Mock()
            return mock

    def test_default_config(self):
        builder = self.StubBuilder()

        self.assertEqual("foo", builder.path)

    def test_setting_valid_path(self):
        builder = cb.FileBasedClientBuilder(__file__)

        self.assertTrue(builder.file_exists)
        self.assertEqual(__file__, builder.path)

    def test_setting_invalid_path(self):
        builder = cb.FileBasedClientBuilder("nowhere")

        with self.assertRaises(IOError):
            builder.build()

        self.assertFalse(builder.file_exists)

    def test_setting_user_path(self):
        builder = cb.FileBasedClientBuilder("~/")

        self.assertEqual(os.path.expanduser("~/"), builder.path)

    def test_logging_in(self):
        client = self.StubBuilder(__file__, True).build()
        client.login.assert_called_once_with("U", "P")

    def test_not_logging_in(self):
        client = self.StubBuilder(__file__, False).build()
        self.assertFalse(client.login.called)


class TestPydoraConfigFileBuilder(TestCase):

    def test_cfg_to_dict(self):
        cfg = Mock()
        cfg.items = Mock(return_value=[("a", "b"), ("c", "d")])

        dct = cb.PydoraConfigFileBuilder.cfg_to_dict(cfg, "foo")

        self.assertEqual("b", dct["A"])
        self.assertEqual("d", dct["C"])

    def test_integration(self):
        path = os.path.join(os.path.dirname(__file__), "pydora.cfg")
        cfg = cb.PydoraConfigFileBuilder(path).parse_config()

        self.assertDictEqual(cfg, {
            "AUDIO_QUALITY": "test_quality",
            "AD_SUPPORT_ENABLED": "test_ad_support",
            "DECRYPTION_KEY": "test_decryption_key",
            "DEVICE": "test_device",
            "ENCRYPTION_KEY": "test_encryption_key",
            "PARTNER_PASSWORD": "test_partner_password",
            "PARTNER_USER": "test_partner_username",
            "API_HOST": "test_host",
            "USER": {
                "USERNAME": "test_username",
                "PASSWORD": "test_password",
                }
            })


class TestPianobarConfigFileBuilder(TestCase):

    def test_integration(self):
        path = os.path.join(os.path.dirname(__file__), "pianobar.cfg")
        cfg = cb.PianobarConfigFileBuilder(path).parse_config()

        self.assertDictEqual(cfg, {
            "AUDIO_QUALITY": "test_qualityQuality",
            "AD_SUPPORT_ENABLED": "test_ad_support",
            "DECRYPTION_KEY": "test_decryption_key",
            "DEVICE": "test_device",
            "ENCRYPTION_KEY": "test_encryption_key",
            "PARTNER_PASSWORD": "test_partner_password",
            "PARTNER_USER": "test_partner_username",
            "API_HOST": "test_host/services/json/",
            "PROXY": "test_proxy",
            "USER": {
                "USERNAME": "test_username",
                "PASSWORD": "test_password",
                }
            })

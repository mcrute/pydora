import sys
import time
import json
import random
import requests
from unittest import TestCase
from pandora.py2compat import Mock, call, patch

from pandora.errors import InvalidAuthToken, PandoraException
from tests.test_pandora.test_clientbuilder import TestSettingsDictBuilder

import pandora.transport as t


class SysCallError(Exception):
    pass


class TestTransport(TestCase):

    def test_test_url_should_return_true_if_request_okay(self):
        transport = t.APITransport(Mock())
        transport._http = Mock()
        transport._http.head.return_value = Mock(
            status_code=requests.codes.not_found)

        self.assertFalse(transport.test_url("foo"))

        transport._http.head.return_value = Mock(status_code=requests.codes.OK)
        self.assertTrue(transport.test_url("foo"))

    def test_call_should_retry_max_times_on_sys_call_error(self):
        with self.assertRaises(SysCallError):
            client = TestSettingsDictBuilder._build_minimal()

            time.sleep = Mock()
            client.transport._make_http_request = Mock(
                    side_effect=SysCallError("error_mock"))
            client.transport._start_request = Mock()

            client("method")

        client.transport._start_request.assert_has_calls([call("method")])
        assert client.transport._start_request.call_count == 3

    def test_call_should_not_retry_for_pandora_exceptions(self):
        with self.assertRaises(PandoraException):
            client = TestSettingsDictBuilder._build_minimal()

            time.sleep = Mock()
            client.transport._make_http_request = Mock(
                    side_effect=PandoraException("error_mock"))
            client.transport._start_request = Mock()

            client("method")

            client.transport._start_request.assert_has_calls([call("method")])
            assert client.transport._start_request.call_count == 1

    def test_call_should_retry_if_auth_token_expired(self):
        with self.assertRaises(InvalidAuthToken):
            client = TestSettingsDictBuilder._build_minimal()

            time.sleep = Mock()
            client.transport._make_http_request = Mock(
                    side_effect=InvalidAuthToken("error_mock"))
            client.transport._start_request = Mock()

            client._authenticate = Mock()

            client("method")

            client.transport._start_request.assert_has_calls([call("method")])
            assert client.transport._start_request.call_count == 2
            assert client._authenticate.call_count == 1

    def test_complete_request(self):
        transport = t.APITransport(Mock())
        transport._http = Mock()

        http_result = Mock()
        http_result.content = b'{"stat":"ok","result":"bar"}'
        transport._http.post.return_value = http_result

        self.assertEqual(
            "bar", transport(t.APITransport.NO_ENCRYPT[0], foo="bar"))


class TestTransportSetters(TestCase):

    def setUp(self):
        self.cryptor = Mock()
        self.transport = t.APITransport(self.cryptor)

    def test_set_partner(self):
        self.cryptor.decrypt_sync_time.return_value = 456

        self.transport.set_partner({
            "syncTime": "123",
            "partnerAuthToken": "partner_auth_token",
            "partnerId": "partner_id",
        })

        self.cryptor.decrypt_sync_time.assert_called_with("123")
        self.assertEqual("partner_auth_token", self.transport.auth_token)
        self.assertEqual("partner_id", self.transport.partner_id)
        self.assertEqual(
            "partner_auth_token", self.transport.partner_auth_token)

        self.transport.start_time = 10
        with patch.object(time, "time", return_value=30):
            self.assertEqual(476, self.transport.sync_time)

    def test_set_user(self):
        self.transport.set_user({
            "userId": "user",
            "userAuthToken": "auth",
        })

        self.assertEqual("user", self.transport.user_id)
        self.assertEqual("auth", self.transport.user_auth_token)
        self.assertEqual("auth", self.transport.auth_token)

    def test_getting_auth_token_no_login(self):
        self.assertIsNone(self.transport.auth_token)
        self.assertIsNone(self.transport.sync_time)


class TestDelayExponential(TestCase):

    def test_fixed_delay(self):
        self.assertEqual(8, t.delay_exponential(2, 2, 3))

    def test_random_delay(self):
        with patch.object(random, "random", return_value=10):
            self.assertEqual(20, t.delay_exponential("rand", 2, 2))

    def test_fails_with_base_zero_or_below(self):
        with self.assertRaises(ValueError):
            t.delay_exponential(0, 1, 1)

        with self.assertRaises(ValueError):
            t.delay_exponential(-1, 1, 1)


class TestRetries(TestCase):

    def test_no_retries_returns_none(self):
        @t.retries(0)
        def foo():
            return True

        self.assertIsNone(foo())


class TestParseResponse(TestCase):

    VALID_MSG_NO_BODY_JSON = b'{"stat":"ok"}'
    VALID_MSG_JSON = b'{"stat":"ok", "result":{"foo":"bar"}}'
    ERROR_MSG_JSON = b'{"stat":"err", "code":1001, "message":"Details"}'

    def setUp(self):
        self.transport = t.APITransport(Mock())

    def test_with_valid_response(self):
        res = self.transport._parse_response(self.VALID_MSG_JSON)
        self.assertEqual({ "foo": "bar" }, res)

    def test_with_valid_response_no_body(self):
        res = self.transport._parse_response(self.VALID_MSG_NO_BODY_JSON)
        self.assertIsNone(res)

    def test_with_error_response(self):
        with self.assertRaises(InvalidAuthToken) as ex:
            self.transport._parse_response(self.ERROR_MSG_JSON)

        self.assertEqual(1001, ex.exception.code)
        self.assertEqual("Details", ex.exception.extended_message)


class TestTransportRequestPrep(TestCase):

    def setUp(self):
        self.cryptor = Mock()
        self.transport = t.APITransport(self.cryptor)

    def test_start_request(self):
        self.transport.start_time = 10
        self.transport._start_request("method_name")
        self.assertEqual(10, self.transport.start_time)

    def test_start_request_with_reset(self):
        self.transport.reset = Mock()
        self.transport._start_request(self.transport.REQUIRE_RESET[0])
        self.transport.reset.assert_called_with()

    def test_start_request_without_time(self):
        with patch.object(time, "time", return_value=10.0):
            self.transport._start_request("method_name")
            self.assertEqual(10, self.transport.start_time)

    def test_make_http_request(self):
        # url, data, params
        http = Mock()
        retval = Mock()
        retval.content = "foo"
        http.post.return_value = retval

        self.transport._http = http
        res = self.transport._make_http_request(
            "/url", b"data", { "a":None, "b":"c" })

        http.post.assert_called_with("/url", data=b"data", params={"b":"c"})
        retval.raise_for_status.assert_called_with()

        self.assertEqual("foo", res)

    def test_build_data_not_logged_in(self):
        self.cryptor.encrypt = lambda x: x

        self.transport.partner_auth_token = "pat"
        self.transport.server_sync_time = 123
        self.transport.start_time = 23

        with patch.object(time, "time", return_value=20):
            val = self.transport._build_data("foo", {"a":"b", "c":None})

        val = json.loads(val)
        self.assertEqual("b", val["a"])
        self.assertEqual("pat", val["partnerAuthToken"])
        self.assertEqual(120, val["syncTime"])

    def test_build_data_no_encrypt(self):
        self.transport.user_auth_token = "uat"
        self.transport.partner_auth_token = "pat"
        self.transport.server_sync_time = 123
        self.transport.start_time = 23

        with patch.object(time, "time", return_value=20):
            val = self.transport._build_data(
                t.APITransport.NO_ENCRYPT[0], {"a":"b", "c":None})

        val = json.loads(val)
        self.assertEqual("b", val["a"])
        self.assertEqual("uat", val["userAuthToken"])
        self.assertEqual(120, val["syncTime"])


# All Cryptor implementations must pass these test cases unmodified
class CommonCryptorTestCases(object):

    def test_decrypt_invalid_padding(self):
        with self.assertRaises(ValueError):
            data = b"12345678\x00"
            self.assertEqual(b"12345678\x00", self.cryptor.decrypt(data))

    def test_decrypt_strip_padding(self):
        data = b"123456\x02\x02"
        self.assertEqual(b"123456", self.cryptor.decrypt(data))

    def test_decrypt_preserve_padding(self):
        data = b"123456\x02\x02"
        self.assertEqual(b"123456\x02\x02", self.cryptor.decrypt(data, False))

    def test_encrypt(self):
        data = "123456"
        self.assertEqual(b"123456\x02\x02", self.cryptor.encrypt(data))


class TestPurePythonBlowfishCryptor(TestCase, CommonCryptorTestCases):

    def setUp(self):
        # Ugh... blowfish can't even be *imported* in python2
        if not t.blowfish:
            t.blowfish = Mock()

        self.cipher = Mock()
        self.cipher.decrypt_ecb = lambda x: [x]
        self.cipher.encrypt_ecb = lambda x: [x]
        self.cryptor = t.PurePythonBlowfish("keys")
        self.cryptor.cipher = self.cipher


class TestCryptographyBlowfish(TestCase, CommonCryptorTestCases):

    class FakeCipher(object):

        def update_into(self, val, buf):
            for i, v in enumerate(val):
                buf[i] = v
            return len(val)

        def finalize(self):
            return b""

    def setUp(self):
        self.cipher = Mock()
        self.cipher.encryptor.return_value = self.FakeCipher()
        self.cipher.decryptor.return_value = self.FakeCipher()
        self.cryptor = t.CryptographyBlowfish("keys")
        self.cryptor.cipher = self.cipher


class TestEncryptor(TestCase):

    ENCODED_JSON = "7b22666f6f223a22626172227d"
    UNENCODED_JSON = b'{"foo":"bar"}'
    EXPECTED_TIME = 4111
    ENCODED_TIME = "31353037343131313539"

    class NoopCrypto(object):

        def __init__(self, key):
            pass

        def decrypt(self, data, strip_padding=True):
            return data.decode("ascii")

        def encrypt(self, data):
            return data

    def setUp(self):
        self.cryptor = t.Encryptor("in", "out", self.NoopCrypto)

    def test_decrypt(self):
        self.assertEqual(
            { "foo": "bar" }, self.cryptor.decrypt(self.ENCODED_JSON))

    def test_encrypt(self):
        self.assertEqual(
            self.ENCODED_JSON.encode("ascii"),
            self.cryptor.encrypt(self.UNENCODED_JSON))

    def test_decrypt_sync_time(self):
        self.assertEqual(
            self.EXPECTED_TIME,
            self.cryptor.decrypt_sync_time(self.ENCODED_TIME))


class TestDefaultStrategy(TestCase):

    def test_blowfish_not_available(self):
        del sys.modules["pandora.transport"]
        sys.modules["blowfish"] = None

        import pandora.transport as t
        self.assertIsNone(t.blowfish)
        self.assertIs(t._default_crypto, t.CryptographyBlowfish)

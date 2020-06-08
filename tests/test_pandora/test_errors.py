from unittest import TestCase

from pandora.errors import InternalServerError, PandoraException


class TestPandoraExceptionConstructionFromErrorCode(TestCase):
    def test_it_returns_specific_error_class_if_possible(self):
        error = PandoraException.from_code(0, "Test Message")
        self.assertIsInstance(error, InternalServerError)
        self.assertEqual("Test Message", error.extended_message)
        self.assertEqual(0, error.code)

    def test_it_returns_generic_error_if_unknown(self):
        error = PandoraException.from_code(-99, "Test Message")
        self.assertIsInstance(error, PandoraException)
        self.assertEqual("Test Message", error.extended_message)

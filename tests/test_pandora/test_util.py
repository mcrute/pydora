import warnings
from unittest import TestCase
from unittest.mock import patch

from pandora import util


class TestDeprecatedWarning(TestCase):

    def test_warning(self):
        class Bar(object):

            @util.deprecated("1.0", "2.0", "Don't use this")
            def foo(self):
                pass

        with patch.object(warnings, "warn") as wmod:
            Bar().foo()

            wmod.assert_called_with(
                ("foo is deprecated as of version 1.0 and will be removed in "
                    "version 2.0. Don't use this"), DeprecationWarning)

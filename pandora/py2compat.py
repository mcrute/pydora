"""
Python 2 Compatibility Layer

This module exists to work around compatibility issues between Python 2 and
Python 3. The main code-base will use Python 3 idioms and this module will
patch Python 2 code to support those changes. When Python 2 support is
dropped this module can be removed and imports can be updated.
"""

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import SafeConfigParser

    class ConfigParser(SafeConfigParser):

        def read_file(self, fp):
            return self.readfp(fp)


# Only used in tests
try:
    from unittest.mock import Mock, MagicMock, call
except ImportError:
    try:
        from mock import Mock, MagicMock, call
    except ImportError:
        pass

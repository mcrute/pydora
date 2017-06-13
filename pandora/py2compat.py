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
    from unittest.mock import Mock, MagicMock, call, patch  # noqa: F401
except ImportError:
    try:
        from mock import Mock, MagicMock, call, patch  # noqa: F401
    except ImportError:
        pass


try:
    from shutil import which
except ImportError:
    import os
    import sys

    # Copypasta from Python 3.6, exists in 3.3+
    def which(cmd, mode=os.F_OK | os.X_OK, path=None):
        def _access_check(fn, mode):
            return (os.path.exists(fn) and os.access(fn, mode)
                    and not os.path.isdir(fn))

        if os.path.dirname(cmd):
            if _access_check(cmd, mode):
                return cmd
            return None

        if path is None:
            path = os.environ.get("PATH", os.defpath)
        if not path:
            return None
        path = path.split(os.pathsep)

        if sys.platform == "win32":
            if os.curdir not in path:
                path.insert(0, os.curdir)

            pathext = os.environ.get("PATHEXT", "").split(os.pathsep)
            if any(cmd.lower().endswith(ext.lower()) for ext in pathext):
                files = [cmd]
            else:
                files = [cmd + ext for ext in pathext]
        else:
            files = [cmd]

        seen = set()
        for dir in path:
            normdir = os.path.normcase(dir)
            if normdir not in seen:
                seen.add(normdir)
                for thefile in files:
                    name = os.path.join(dir, thefile)
                    if _access_check(name, mode):
                        return name
        return None

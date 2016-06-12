"""
Utility Functions

Functions that don't have a home anywhere else.
"""

import warnings
from functools import wraps


def warn_deprecated(in_version, remove_version, what, message):
    """Warn that something is deprecated
    """
    msg = ("{} is deprecated as of version {}"
           " and will be removed in version {}. {}")

    warnings.warn(
        msg.format(what, in_version, remove_version, message),
        DeprecationWarning)


def deprecated(in_version, remove_version, message):
    """Deprecated function decorator

    Decorator to warn that a function is deprecated and what version it will be
    removed in.
    """
    def wrapper(wrapped):
        @wraps(wrapped)
        def inner_wrapper(self, *args, **kwargs):
            warn_deprecated(
                in_version, remove_version, wrapped.func_name, message)
            return wrapped(self, *args, **kwargs)
        return inner_wrapper
    return wrapper

"""
Pandora API Exceptions

This module contains the API exceptions from the Pandora API. The exception
classes are automatically generated from the API spec below and are added to
this module at first import. Exceptions will always be a sub-class of the base
PandoraException.

The name of the exception class is the message name with space removed and each
word capitalized. If the exception message contains a dash the class name will
not contain the dash or anything that follows it.
"""

__API_EXCEPTIONS__ = {
    0: "Internal Server Error",
    1: "Maintenance Mode",
    2: "Missing API Method",
    3: "Missing Auth Token",
    4: "Missing Partner ID",
    5: "Missing User ID",
    6: "Secure Protocol Required",
    7: "Certificate Required",
    8: "Parameter Type Mismatch",
    9: "Parameter Missing",
    10: "Parameter Value Invalid",
    11: "API Version Not Supported",
    12: "Pandora not available in this country",
    13: "Bad Sync Time",
    14: "Unknown Method Name",
    15: "Wrong Protocol - (http/https)",
    1000: "Read Only Mode",
    1001: "Invalid Auth Token",
    1002: "Invalid Partner Login",
    1003: "Listener Not Authorized - Subscription or Trial Expired",
    1004: "User Not Authorized",
    1005: "Station limit reached",
    1006: "Station does not exist",
    1009: "Device Not Found",
    1010: "Partner Not Authorized",
    1011: "Invalid Username",
    1012: "Invalid Password",
    1023: "Device Model Invalid",
    1039: "Too many requests for a new playlist",
    9999: "Authentication Required",
}


class PandoraException(Exception):
    """Pandora API Exception

    Translates exceptions to user readable info.
    """

    code = None
    message = "Unknown Exception"

    def __init__(self, extended_message=""):
        self.extended_message = extended_message
        super(Exception, self).__init__(self.message)

    @classmethod
    def from_code(cls, code, extended_message):
        exc = __API_EXCEPTIONS__.get(code)

        if not exc:
            exc = PandoraException(extended_message)
            exc.code = code
            return exc
        else:
            return exc(extended_message)

    @staticmethod
    def _format_name(name):
        output = []

        for part in name.split(" "):
            if part == "-":
                break
            else:
                output.append(part.capitalize())

        return "".join(output)

    @staticmethod
    def export_exceptions(export_to):
        for code, api_message in __API_EXCEPTIONS__.items():
            name = PandoraException._format_name(api_message)

            exception = type(name, (PandoraException,), {
                "code": code,
                "message": api_message,
            })

            export_to[name] = __API_EXCEPTIONS__[code] = exception


PandoraException.export_exceptions(locals())


class InvalidUserLogin(InvalidPartnerLogin):  # noqa: F821
    """Pydora Internal Login Error

    This is thrown around a user login to disambiguate a login that is invalid
    due to user error vs a login that is invalid due to a partner credential
    error. The Pandora API returns 1002 in both cases.
    """

    message = "Invalid User Login"

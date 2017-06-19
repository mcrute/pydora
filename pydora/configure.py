import os
import re
import sys
import requests

from pandora.client import APIClient
from pandora.py2compat import ConfigParser
from pandora.clientbuilder import PydoraConfigFileBuilder

from .utils import Screen, Colors


class Umask(object):
    """Set/Restore Umask Context Manager
    """

    def __init__(self, umask):
        self.umask = umask
        self.old_umask = None

    def __enter__(self):
        self.old_umask = os.umask(self.umask)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.umask(self.old_umask)


class PandoraKeysConfigParser(object):
    """Parser for Pandora Keys Source Page

    This is an extremely naive restructured text parser designed only to parse
    the pandora API docs keys source file.
    """

    KEYS_URL = ("http://6xq.net/git/lars/pandora-apidoc.git/"
                "plain/json/partners.rst")

    FIELD_RE = re.compile(
        ":(?P<key>[^:]+): (?:`{2})?(?P<value>[^`\n]+)(?:`{2})?$")

    def _fixup_key(self, key):
        key = key.lower()

        if key.startswith("dec") and "password" in key:
            return "decryption_key"
        elif key.startswith("encrypt"):
            return "encryption_key"
        elif key == "deviceid":
            return "device"
        else:
            return key

    def _format_api_host(self, host):
        return "{}/services/json/".format(host)

    def _clean_device_name(self, name):
        return re.sub("[^a-z]+", "_", name, flags=re.I)

    def _fetch_config(self):
        return requests.get(self.KEYS_URL).text.split("\n")

    def _match_key(self, line):
        key_match = self.FIELD_RE.match(line)
        if key_match:
            match = key_match.groupdict()
            match["key"] = self._fixup_key(match["key"])
            return match
        else:
            return None

    def _is_host_terminator(self, line):
        return line.startswith("--")

    def _is_device_terminator(self, line):
        return line.startswith("^^")

    def load(self):
        buffer = []
        current_partner = {}
        api_host = None
        partners = {}

        for line in self._fetch_config():
            key_match = self._match_key(line)
            if key_match:
                current_partner[key_match["key"]] = key_match["value"]
            elif self._is_host_terminator(line):
                api_host = buffer.pop()
            elif self._is_device_terminator(line):
                key = self._clean_device_name(buffer.pop())
                current_partner = partners[key] = {
                    "api_host": self._format_api_host(api_host)
                    }

            buffer.append(line.strip().lower())

        return partners


class Configurator(object):
    """Interactive Configuration Builder

    Allows a user to configure pydora interactively. Ultimately writes the
    pydora config file.
    """

    def __init__(self):
        self.builder = PydoraConfigFileBuilder()

        self.cfg = ConfigParser()

        if self.builder.file_exists:
            self.read_config()
        else:
            self.cfg.add_section("user")
            self.cfg.add_section("api")

    def fail(self, message):
        print(Screen.print_error(message))
        sys.exit(1)

    def finished(self, message):
        Screen.print_success(message)
        sys.exit(0)

    def print_message(self, message):
        print(Colors.cyan(message))

    def get_partner_config(self):
        try:
            return PandoraKeysConfigParser().load()["android"]
        except:
            self.fail("Error loading config file. Unable to continue.")

    def get_value(self, section, key, prompt):
        self.cfg.set(section, key, Screen.get_string(prompt))

    def get_password(self, section, key, prompt):
        self.cfg.set(section, key, Screen.get_password(prompt))

    def set_static_value(self, section, key, value):
        self.cfg.set(section, key, value)

    def add_partner_config(self, config):
        for key, value in config.items():
            self.cfg.set("api", key, value)

    def read_config(self):
        with open(self.builder.path) as file:
            self.cfg.read_file(file)

    def write_config(self):
        with Umask(0o077), open(self.builder.path, "w") as file:
            self.cfg.write(file)

    def configure(self):
        if self.builder.file_exists:
            self.print_message("You already have a pydora config.")
            self.add_partner_config(self.get_partner_config())
            self.write_config()
            self.finished("Freshened your API keys!")

        self.print_message("Welcome to Pydora, let's configure a few things")
        self.add_partner_config(self.get_partner_config())
        self.get_value("user", "username", "Pandora Username: ")
        self.get_password("user", "password", "Pandora Password: ")
        self.set_static_value("api", "default_audio_quality",
                              APIClient.HIGH_AUDIO_QUALITY)

        self.write_config()


def main():
    Configurator().configure()

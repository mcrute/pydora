import os
import re
import sys
import requests
from configparser import ConfigParser

from pandora.client import APIClient
from pandora.clientbuilder import PydoraConfigFileBuilder

from .utils import Screen, Colors


class Umask:
    """Set/Restore Umask Context Manager"""

    def __init__(self, umask):
        self.umask = umask
        self.old_umask = None

    def __enter__(self):
        self.old_umask = os.umask(self.umask)

    def __exit__(self, exc_type, exc_val, exc_tb):
        os.umask(self.old_umask)


# Public Android defaults from Pianobar's src/settings.c.
PIANOBAR_SETTINGS_URL = (
    "https://raw.githubusercontent.com/PromyLOPh/pianobar/master/src/settings.c"
)
ANDROID_PARTNER_DEFAULTS = {
    "api_host": "tuner.pandora.com/services/json/",
    "username": "android",
    "password": "AC7IBG09A3DTSYM4R41UJWL07VLN8JI7",
    "device": "android-generic",
    "decryption_key": "R=U!LH$O2B#",
    "encryption_key": "6#26FRL$ZWD",
}
PIANOBAR_FIELDS = {
    "partnerUser": "username",
    "partnerPassword": "password",
    "device": "device",
    "inkey": "decryption_key",
    "outkey": "encryption_key",
}


def load_partner_config():
    """Read the Android partner profile from Pianobar's master branch."""
    response = requests.get(PIANOBAR_SETTINGS_URL, timeout=10)
    response.raise_for_status()
    config = {"api_host": ANDROID_PARTNER_DEFAULTS["api_host"]}
    for field, option in PIANOBAR_FIELDS.items():
        match = re.search(
            r'^\s*settings->' + field + r' = strdup \("([^"\\]+)"\);',
            response.text,
            re.MULTILINE,
        )
        if not match:
            raise ValueError("Missing Pianobar default for " + field)
        config[option] = match.group(1)
    return config


class Configurator:
    """Interactive Configuration Builder

    Allows a user to configure pydora interactively. Ultimately writes the
    pydora config file.
    """

    def __init__(self):
        self.builder = PydoraConfigFileBuilder()

        self.cfg = ConfigParser()
        self.screen = Screen()

        if self.builder.file_exists:
            self.read_config()
        else:
            self.cfg.add_section("user")
            self.cfg.add_section("api")

    def fail(self, message):
        self.screen.print_error(message)
        sys.exit(1)

    def finished(self, message):
        self.screen.print_success(message)
        sys.exit(0)

    def print_message(self, message):
        print(Colors.cyan(message))

    def get_partner_config(self):
        try:
            return load_partner_config()
        except (requests.RequestException, ValueError):
            self.print_message("Using bundled Android partner settings.")
            return ANDROID_PARTNER_DEFAULTS.copy()

    def get_value(self, section, key, prompt):
        self.cfg.set(section, key, self.screen.get_string(prompt))

    def get_password(self, section, key, prompt):
        self.cfg.set(section, key, self.screen.get_password(prompt))

    def set_static_value(self, section, key, value):
        self.cfg.set(section, key, value)

    def add_partner_config(self, config):
        for key, value in config.items():
            self.cfg.set("api", key, value)
        for alias, key in (("partner_user", "username"),
                           ("partner_password", "password")):
            if self.cfg.has_option("api", alias):
                self.cfg.set("api", alias, config[key])

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
        self.set_static_value(
            "api", "default_audio_quality", APIClient.HIGH_AUDIO_QUALITY
        )

        self.write_config()


def main():
    Configurator().configure()

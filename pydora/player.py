#!/usr/bin/env python
"""
Sample Barebones Pandora Player

This is a very simple Pandora player that streams music from Pandora. It
requires mpg123 or VLC to function. No songs are downloaded, they are streamed
directly from Pandora's servers.
"""
from __future__ import print_function

import os
import sys
from pandora import clientbuilder

from .utils import Colors, Screen
from .audio_backend import MPG123Player, VLCPlayer
from .audio_backend import UnsupportedEncoding, PlayerUnusable


class PlayerCallbacks(object):
    """Interface for Player Callbacks

    This class simply exists to document the interface for callback
    implementers implementers need not extend this class.
    """

    def play(self, song):
        """Called once when a song starts playing
        """
        pass

    def pre_poll(self):
        """Called before polling for process status
        """
        pass

    def post_poll(self):
        """Called after polling for process status
        """
        pass

    def input(self, value, song):
        """Called after user input during song playback
        """
        pass


class PlayerApp(object):

    CMD_MAP = {
        "n": ("play next song", "skip_song"),
        "p": ("pause/resume song", "pause_song"),
        "s": ("stop playing station", "stop_station"),
        "d": ("dislike song", "dislike_song"),
        "u": ("like song", "like_song"),
        "b": ("bookmark song", "bookmark_song"),
        "a": ("bookmark artist", "bookmark_artist"),
        "S": ("sleep song for 30 days", "sleep_song"),
        "Q": ("quit player", "quit"),
        "vu": ("raise volume", "raise_volume"),
        "vd": ("lower volume", "lower_volume"),
        "?": ("display this help", "help"),
    }

    def __init__(self):
        self.client = None

    def get_player(self):
        try:
            player = VLCPlayer(self, sys.stdin)
            Screen.print_success("Using VLC")
            return player
        except PlayerUnusable:
            pass

        try:
            player = MPG123Player(self, sys.stdin)
            Screen.print_success("Using mpg123")
            return player
        except PlayerUnusable:
            pass

        Screen.print_error("Unable to find a player")
        sys.exit(1)

    def get_client(self):
        cfg_file = os.environ.get("PYDORA_CFG", "")
        builder = clientbuilder.PydoraConfigFileBuilder(cfg_file)
        if builder.file_exists:
            return builder.build()

        builder = clientbuilder.PianobarConfigFileBuilder()
        if builder.file_exists:
            return builder.build()

        if not self.client:
            Screen.print_error("No valid config found")
            sys.exit(1)

    def station_selection_menu(self, error=None):
        """Format a station menu and make the user select a station
        """
        Screen.clear()

        if error:
            Screen.print_error("{}\n".format(error))

        for i, station in enumerate(self.stations):
            i = "{:>3}".format(i)
            print(u"{}: {}".format(Colors.yellow(i), station.name))

        return self.stations[Screen.get_integer("Station: ")]

    def play(self, song):
        """Play callback
        """
        if song.is_ad:
            print(u"{} ".format(Colors.cyan("Advertisement")))
        else:
            print(u"{} by {}".format(Colors.cyan(song.song_name),
                                     Colors.yellow(song.artist_name)))

    def skip_song(self, song):
        if song.is_ad:
            Screen.print_error("Cannot skip advertisements")
        else:
            self.player.stop()

    def pause_song(self, song):
        self.player.pause()

    def stop_station(self, song):
        self.player.end_station()

    def dislike_song(self, song):
        try:
            if song.thumbs_down():
                Screen.print_success("Track disliked")
                self.player.stop()
            else:
                Screen.print_error("Failed to dislike track")
        except NotImplementedError:
            Screen.print_error("Cannot dislike this type of track")

    def like_song(self, song):
        try:
            if song.thumbs_up():
                Screen.print_success("Track liked")
            else:
                Screen.print_error("Failed to like track")
        except NotImplementedError:
            Screen.print_error("Cannot like this type of track")

    def bookmark_song(self, song):
        try:
            if song.bookmark_song():
                Screen.print_success("Bookmarked song")
            else:
                Screen.print_error("Failed to bookmark song")
        except NotImplementedError:
            Screen.print_error("Cannot bookmark this type of track")

    def bookmark_artist(self, song):
        try:
            if song.bookmark_artist():
                Screen.print_success("Bookmarked artist")
            else:
                Screen.print_error("Failed to bookmark artis")
        except NotImplementedError:
            Screen.print_error("Cannot bookmark artist for this type of track")

    def sleep_song(self, song):
        try:
            if song.sleep():
                Screen.print_success("Song will not be played for 30 days")
                self.player.stop()
            else:
                Screen.print_error("Failed to sleep song")
        except NotImplementedError:
            Screen.print_error("Cannot sleep this type of track")

    def raise_volume(self, song):
        try:
            self.player.raise_volume()
        except NotImplementedError:
            Screen.print_error("Cannot sleep this type of track")

    def lower_volume(self, song):
        try:
            self.player.lower_volume()
        except NotImplementedError:
            Screen.print_error("Cannot sleep this type of track")

    def quit(self, song):
        self.player.end_station()
        sys.exit(0)

    def help(self, song):
        print("")
        print("\n".join([
            "\t{:>2} - {}".format(k, v[0])
            for k, v in sorted(self.CMD_MAP.items())
        ]))
        print("")

    def input(self, input, song):
        """Input callback, handles key presses
        """
        try:
            cmd = getattr(self, self.CMD_MAP[input][1])
        except (IndexError, KeyError):
            return Screen.print_error("Invalid command {!r}!".format(input))

        cmd(song)

    def pre_poll(self):
        Screen.set_echo(False)

    def post_poll(self):
        Screen.set_echo(True)

    def pre_flight_checks(self):
        # See #52, this key no longer passes some server-side check
        if self.client.partner_user == "iphone":
            Screen.print_error((
                "The `iphone` partner key set is no longer compatible with "
                "pydora. Please re-run pydora-configure to re-generate "
                "your config file before continuing."))
            sys.exit(1)

    def run(self):
        self.player = self.get_player()
        self.player.start()

        self.client = self.get_client()
        self.stations = self.client.get_station_list()

        self.pre_flight_checks()

        error = None

        while True:
            try:
                station = self.station_selection_menu(error)
                error = None
            except IndexError:
                error = "Invalid station selection."
                continue
            except KeyboardInterrupt:
                sys.exit(0)

            try:
                self.player.play_station(station)
            except UnsupportedEncoding as ex:
                error = str(ex)
            except KeyboardInterrupt:
                sys.exit(0)


def main():
    PlayerApp().run()

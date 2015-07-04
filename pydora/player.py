#!/usr/bin/env python
"""
Sample Barebones Pandora Player

This is a very simple Pandora player that streams music from Pandora. It
requires mpg123 to function. No songs are downloaded, they are streamed
directly from Pandora's servers.
"""
from __future__ import print_function

import os
import sys
from pandora import APIClient, clientbuilder

from .mpg123 import Player
from .utils import Colors, Screen


class PlayerApp(object):

    CMD_MAP = {
        'n': ('play next song', 'skip_song'),
        'p': ('pause/resume song', 'pause_song'),
        's': ('stop playing station', 'stop_station'),
        'd': ('dislike song', 'dislike_song'),
        'u': ('like song', 'like_song'),
        'b': ('bookmark song', 'bookmark_song'),
        'a': ('bookmark artist', 'bookmark_artist'),
        'S': ('sleep song for 30 days', 'sleep_song'),
        'Q': ('quit player', 'quit'),
        '?': ('display this help', 'help'),
    }

    def __init__(self):
        self.client = None
        self.player = Player(self, sys.stdin)

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

    def station_selection_menu(self):
        """Format a station menu and make the user select a station
        """
        Screen.clear()

        for i, s in enumerate(self.stations):
            i = '{:>3}'.format(i)
            print('{}: {}'.format(Colors.yellow(i), s.name))

        return self.stations[Screen.get_integer('Station: ')]

    def play(self, song):
        """Play callback
        """
        print(u'{} by {}'.format(Colors.cyan(song.song_name),
            Colors.yellow(song.artist_name)))

    def skip_song(self, song):
        self.player.stop()

    def pause_song(self, song):
        self.player.pause()

    def stop_station(self, song):
        self.player.end_station()

    def dislike_song(self, song):
        song.thumbs_down()
        Screen.print_success('Track disliked')
        self.player.stop()

    def like_song(self, song):
        song.thumbs_up()
        Screen.print_success('Track liked')

    def bookmark_song(self, song):
        song.bookmark_song()
        Screen.print_success('Bookmarked song')

    def bookmark_artist(self, song):
        song.bookmark_artist()
        Screen.print_success('Bookmarked artist')

    def sleep_song(self, song):
        song.sleep()
        Screen.print_success('Song will not be played for 30 days')
        self.player.stop()

    def quit(self, song):
        self.player.end_station()
        sys.exit(0)

    def help(self, song):
        print("")
        print("\n".join([
            "\t{} - {}".format(k, v[0]) for k, v in self.CMD_MAP.items()
        ]))
        print("")

    def input(self, input, song):
        """Input callback, handles key presses
        """
        try:
            cmd = getattr(self, self.CMD_MAP[input][1])
        except (IndexError, KeyError):
            return Screen.print_error('Invalid command!')

        cmd(song)

    def pre_poll(self):
        Screen.set_echo(False)

    def post_poll(self):
        Screen.set_echo(True)

    def run(self):
        self.client = self.get_client()
        self.stations = self.client.get_station_list()

        while True:
            try:
                station = self.station_selection_menu()
                self.player.play_station(station)
            except KeyboardInterrupt:
                sys.exit(0)


def main():
    PlayerApp().run()


if __name__ == '__main__':
    main()

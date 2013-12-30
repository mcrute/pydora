#!/usr/bin/env python
"""
Sample Barebones Pandora Player

This is a very simple Pandora player that streams music from Pandora. It
requires mpg123 to function. No songs are downloaded, they are streamed
directly from Pandora's servers.

This player requires a settings.py file with a SETTINGS dictionary (see
pandora.py for format), a USERNAME and a PASSWORD that are your Pandora
username and password.
"""
import sys
import settings

from pandora import APIClient
from pandora.player import Player
from pandora.utils import Colors, Screen


class PlayerApp:

    def __init__(self):
        self.client = APIClient.from_settings_dict(settings.SETTINGS)
        self.player = Player(self, sys.stdin)

    def station_selection_menu(self):
        """Format a station menu and make the user select a station
        """
        Screen.clear()

        for i, s in enumerate(self.stations):
            i = '{:>3}'.format(i)
            print('{}: {}'.format(Colors.yellow(i), s.name))

        return self.stations[Screen.get_integer('Station: ')]

    def play(self, song):
        """Play callback, prints song name
        """
        print('{} by {}'.format(Colors.blue(song.song_name),
            Colors.yellow(song.artist_name)))

    def input(self, input, song):
        """Input callback, handles key presses
        """
        if input == 'n':
            self.player.stop()
        elif input == 'p':
            self.player.pause()
        elif input == 's':
            self.player.end_station()
        elif input == 'd':
            song.thumbs_down()
            Screen.print_success('Track disliked')
            self.player.stop()
        elif input == 'u':
            song.thumbs_up()
            Screen.print_success('Track disliked')
        elif input == 'b':
            song.bookmark_song()
            Screen.print_success('Bookmarked song')
        elif input == 'a':
            song.bookmark_artist()
            Screen.print_success('Bookmarked artist')
        elif input == 'S':
            song.sleep()
            Screen.print_success('Song will not be played for 30 days')
            self.player.stop()
        elif input == 'Q':
            self.player.end_station()
            sys.exit(0)

    def run(self):
        """Main run loop of the program
        """
        self.client.login(settings.USERNAME, settings.PASSWORD)
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

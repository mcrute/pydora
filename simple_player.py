"""
Sample Barebones Pandora Player

This is a very simple Pandora player that streams music from Pandora. It
requires mpg123 to function. No songs are downloaded, they are streamed
directly from Pandora's servers.

This player requires a settings.py file with a SETTINGS dictionary (see
pandora.py for format), a USERNAME and a PASSWORD that are your Pandora
username and password.

When playing the following keys work:

    n - next song
    s - station list
    Q - quit program
"""
import sys
import select
import settings
import subprocess
from pandora import APIClient


def iterate_forever(func, *args, **kwargs):
    output = func(*args, **kwargs)

    while True:
        try:
            yield output.next()
        except StopIteration:
            output = func(*args, **kwargs)


class Player(object):

    def __init__(self, station, play_input_callback):
        self.station = station
        self._process = None
        self._play_callback = play_input_callback

    @property
    def playlist(self):
        return iterate_forever(self.station.get_playlist)

    def stop(self):
        self._process.kill()

    def play(self, song):
        print song.song_name, 'by', song.artist_name
        self._process = subprocess.Popen(['mpg123', '-q', song.audio_url])

    def get_input(self):
        while self._process.poll() is None:
            read, _, _ = select.select([sys.stdin], [], [], 1.0)

            if not read:
                continue

            return read[0].readline().strip()

    def end_playlist(self):
        raise StopIteration

    def play_playlist(self):
        for song in self.playlist:
            self.play(song)

            try:
                self._play_callback(self, self.get_input())
            except StopIteration:
                self.stop()
                return


def clear_screen():
    sys.stdout.write('\x1b[2J\x1b[H')
    sys.stdout.flush()


def input_integer(prompt):
    while True:
        try:
            return int(raw_input(prompt).strip())
        except ValueError:
            print 'Invaid Input!'


def station_selection_menu(stations):
    clear_screen()

    for i, s in enumerate(stations):
        print '{}: {}'.format(i, s.name)

    return stations[input_integer('Station: ')]


def main():
    client = APIClient.from_settings_dict(settings.SETTINGS)
    client.login(settings.USERNAME, settings.PASSWORD)
    stations = client.get_station_list()

    def callback(player, input):
        if input == 'n':
            player.stop()
        elif input == 's':
            player.end_playlist()
        elif input == 'Q':
            player.end_playlist()
            sys.exit(0)

    while True:
        try:
            station = station_selection_menu(stations)
            Player(station, callback).play_playlist()
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == '__main__':
    main()

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
    """Iterate over a finite iterator forever

    When the iterator is exhausted will call the function again to generate a
    new iterator and keep iterating.
    """
    output = func(*args, **kwargs)

    while True:
        try:
            yield output.next()
        except StopIteration:
            output = func(*args, **kwargs)


class Player(object):

    def __init__(self, station, input_cb, play_cb):
        """Initialize the player

        station
            The Pandora station object

        input_cb
            Callback that will be called when input occurs during play. Should
            accept two parameters: the player and the input string.

        play_cb
            Callback that will be called when a song starts playing. Should
            accept two parameters: the player and the song model.
        """
        self.station = station
        self._process = None
        self._input_cb = input_cb
        self._play_cb = play_cb

    @property
    def playlist(self):
        """Get a infinite playlist

        This function will iterate forever, calling back to Pandora to get a
        new playlist when it exhausts the previous one.
        """
        return iterate_forever(self.station.get_playlist)

    def stop(self):
        """Stop the currently playing song
        """
        self._process.kill()

    def play(self, song):
        """Play a new song from a Pandora model
        """
        self._play_cb(self, song)
        self._process = subprocess.Popen(['mpg123', '-q', song.audio_url])

    def get_input(self):
        """Get user input while the player is running

        User input must be newline terminated. Returns None when the song ends.
        """
        while self._process.poll() is None:
            read, _, _ = select.select([sys.stdin], [], [], 1.0)

            if not read:
                continue

            return read[0].readline().strip()

    def end_playlist(self):
        """Stop playing the playlist
        """
        raise StopIteration

    def play_playlist(self):
        """Play the playlist until something ends it

        This function will run forever until termintated by calling
        end_playlist.
        """
        for song in self.playlist:
            self.play(song)

            try:
                self._input_cb(self, self.get_input())
            except StopIteration:
                self.stop()
                return


def clear_screen():
    """Clear the terminal
    """
    sys.stdout.write('\x1b[2J\x1b[H')
    sys.stdout.flush()


def input_integer(prompt):
    """Gather user input and convert it to an integer

    Will keep trying till the user enters an interger or until they ^C the
    program.
    """
    while True:
        try:
            return int(raw_input(prompt).strip())
        except ValueError:
            print 'Invaid Input!'


def station_selection_menu(stations):
    """Format a station menu and make the user select a station
    """
    clear_screen()

    for i, s in enumerate(stations):
        print '{}: {}'.format(i, s.name)

    return stations[input_integer('Station: ')]


def main():
    client = APIClient.from_settings_dict(settings.SETTINGS)
    client.login(settings.USERNAME, settings.PASSWORD)
    stations = client.get_station_list()

    def play_cb(player, song):
        print song.song_name, 'by', song.artist_name

    def input_cb(player, input):
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
            Player(station, input_cb, play_cb).play_playlist()
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == '__main__':
    main()

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
import os
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


class SilentPopen(subprocess.Popen):
    """A Popen varient that dumps it's output and error
    """

    def __init__(self, *args, **kwargs):
        self._dev_null = open(os.devnull, 'w')
        kwargs['stdin'] = subprocess.PIPE
        kwargs['stdout'] = subprocess.PIPE
        kwargs['stderr'] = self._dev_null
        super(SilentPopen, self).__init__(*args, **kwargs)

    def __del__(self):
        self._dev_null.close()
        super(SilentPopen, self.__del__)


class Player(object):
    """Remote control for an mpg123 process

    Starts and owns a handle to an mpg123 process then feeds commands to it to
    play pandora audio
    """

    def __init__(self, callbacks):
        self._callbacks = callbacks(self)
        self._process = None
        self._ensure_started()

    def __del__(self):
        self._process.kill()

    def _ensure_started(self):
        """Ensure mpg123 is started
        """
        if self._process and self._process.poll() is None:
            return

        self._process = SilentPopen(
                ['mpg123', '-q', '-R', '--preload', '0.1'])

        # Only output play status in the player stdout
        self._send_cmd('silence')

    def _send_cmd(self, cmd):
        """Write command to remote mpg123 process
        """
        self._process.stdin.write("{}\n".format(cmd))
        self._process.stdin.flush()

    def stop(self):
        """Stop the currently playing song
        """
        self._send_cmd('stop')

    def pause(self):
        """Pause the player
        """
        self._send_cmd('pause')

    def _player_stopped(self, value):
        """Determine if player has stopped
        """
        return value.startswith("@P") and value[3] == "0"

    def play(self, song):
        """Play a new song from a Pandora model

        Returns once the stream starts but does not shut down the remote mpg123
        process. Calls the input callback when the user has input.
        """
        self._callbacks.play(song)
        self._send_cmd('load {}'.format(song.audio_url))

        while True:
            self._ensure_started()

            readers, _, _ = select.select([sys.stdin, self._process.stdout],
                    [], [], 1.0)

            for fd in readers:
                value = fd.readline().strip()

                if fd.fileno() == 0:
                    self._callbacks.input(value)
                else:
                    if self._player_stopped(value):
                        return

    def end_station(self):
        """Stop playing the station
        """
        raise StopIteration

    def play_station(self, station):
        """Play the station until something ends it

        This function will run forever until termintated by calling
        end_station.
        """
        for song in iterate_forever(station.get_playlist):
            try:
                self.play(song)
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

    class PlayerCallbacks:

        def __init__(self, player):
            self.player = player

        def play(self, song):
            print song.song_name, 'by', song.artist_name

        def input(self, input):
            if input == 'n':
                self.player.stop()
            elif input == 'p':
                self.player.pause()
            elif input == 's':
                self.player.end_station()
            elif input == 'Q':
                self.player.end_station()
                sys.exit(0)

    player = Player(PlayerCallbacks)
    while True:
        try:
            station = station_selection_menu(stations)
            player.play_station(station)
        except KeyboardInterrupt:
            sys.exit(0)


if __name__ == '__main__':
    main()

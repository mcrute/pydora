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
from pandora import APIClient

from utils import Colors, iterate_forever, SilentPopen, Screen


class Player(object):
    """Remote control for an mpg123 process

    Starts and owns a handle to an mpg123 process then feeds commands to it to
    play pandora audio
    """

    def __init__(self, callbacks):
        self._callbacks = callbacks
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
                    self._callbacks.input(value, song)
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


class PlayerApp:

    def __init__(self):
        self.client = APIClient.from_settings_dict(settings.SETTINGS)
        self.player = Player(self)

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
            Screen.print_success("Track thumbs'd down")
            self.player.stop()
        elif input == 'u':
            song.thumbs_up()
            Screen.print_success("Track thumbs'd up")
        elif input == 'b':
            song.bookmark_song()
            Screen.print_success("Bookmarked song")
        elif input == 'a':
            song.bookmark_artist()
            Screen.print_success("Bookmarked artist")
        elif input == 'S':
            song.sleep()
            Screen.print_success("Song will not be played for 30 days")
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


if __name__ == '__main__':
    PlayerApp().run()

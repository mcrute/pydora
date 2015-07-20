import select

from .utils import iterate_forever, SilentPopen


class Player(object):
    """Remote control for an mpg123 process

    Starts and owns a handle to an mpg123 process then feeds commands to it to
    play pandora audio
    """

    def __init__(self, callbacks, control_channel):
        self._control_channel = control_channel
        self._control_fd = control_channel.fileno()
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
            ["mpg123", "-q", "-R", "--ignore-mime"])

        # Only output play status in the player stdout
        self._send_cmd("silence")

    def _send_cmd(self, cmd):
        """Write command to remote mpg123 process
        """
        self._process.stdin.write("{}\n".format(cmd).encode("utf-8"))
        self._process.stdin.flush()

    def stop(self):
        """Stop the currently playing song
        """
        self._send_cmd("stop")

    def pause(self):
        """Pause the player
        """
        self._send_cmd("pause")

    def _player_stopped(self, value):
        """Determine if player has stopped
        """
        return value.startswith(b"@P") and value.decode("utf-8")[3] == "0"

    def play(self, song):
        """Play a new song from a Pandora model

        Returns once the stream starts but does not shut down the remote mpg123
        process. Calls the input callback when the user has input.
        """
        self._callbacks.play(song)
        self._send_cmd("load {}".format(song.audio_url))

        while True:
            try:
                self._callbacks.pre_poll()
                self._ensure_started()

                readers, _, _ = select.select(
                    [self._control_channel, self._process.stdout], [], [], 1)

                for fd in readers:
                    value = fd.readline().strip()

                    if fd.fileno() == self._control_fd:
                        self._callbacks.input(value, song)
                    else:
                        if self._player_stopped(value):
                            return
            finally:
                self._callbacks.post_poll()

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

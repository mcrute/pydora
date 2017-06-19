import os
import time
import fcntl
import select

from pandora.py2compat import which
from .utils import iterate_forever, SilentPopen


class PlayerException(Exception):
    """Base class for all player exceptions
    """
    pass


class UnsupportedEncoding(PlayerException):
    """Song encoding is not supported by player backend
    """
    pass


class PlayerUnusable(PlayerException):
    """Player can not be used on this system
    """
    pass


class BasePlayer(object):
    """Audio Backend Process Manager

    Starts and owns a handle to an audio backend process then feeds commands to
    it to play pandora audio. This class provides all the base functionality
    for managing the process and feeding it input but should be subclassed to
    fill in the rest of the interface that is specific to a backend.

    Consumers should call start before using the class to pre-start the command
    and decrease response latency when the first play command is sent.
    """

    def __init__(self, callbacks, control_channel):
        """Constructor

        Will attempt to find the player binary on construction and fail if it
        is not found. Subclasses should append any additional arguments to
        _cmd.
        """
        self._control_channel = control_channel
        self._control_fd = control_channel.fileno()
        self._callbacks = callbacks
        self._process = None
        self._cmd = [self._find_path()]

    def _find_path(self):
        """Find the path to the backend binary

        This method may fail with a PlayerUnusable exception in which case the
        consumer should opt for another backend.
        """
        raise NotImplementedError

    def _load_track(self, song):
        """Load a track into the audio backend by song model
        """
        raise NotImplementedError

    def _player_stopped(self, value):
        """Determine if player has stopped
        """
        raise NotImplementedError

    def raise_volume(self):
        """Raise the volume of the audio output

        The player backend may not support this functionality in which case it
        should not override this method.
        """
        raise NotImplementedError

    def lower_volume(self):
        """Lower the volume of the audio output

        The player backend may not support this functionality in which case it
        should not override this method.
        """
        raise NotImplementedError

    def _post_start(self):
        """Optionally, do something after the audio backend is started
        """
        return

    def _loop_hook(self):
        """Optionally, do something each main loop iteration
        """
        return

    def _read_from_process(self, handle):
        """Read a line from the process and clean it

        Different audio backends return text in different formats so provides a
        hook for each subclass to customize reader behaviour.
        """
        return handle.readline().strip()

    def _send_cmd(self, cmd):
        """Write command to remote process
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

    def __del__(self):
        if self._process:
            self._process.kill()

    def start(self):
        """Start the audio backend process for the player

        This is just a friendlier API for consumers
        """
        self._ensure_started()

    def _ensure_started(self):
        """Ensure player backing process is started
        """
        if self._process and self._process.poll() is None:
            return

        if not getattr(self, "_cmd"):
            raise RuntimeError("Player command is not configured")

        self._process = SilentPopen(self._cmd)
        self._post_start()

    def play(self, song):
        """Play a new song from a Pandora model

        Returns once the stream starts but does not shut down the remote audio
        output backend process. Calls the input callback when the user has
        input.
        """
        self._callbacks.play(song)
        self._load_track(song)
        time.sleep(2)  # Give the backend time to load the track

        while True:
            try:
                self._callbacks.pre_poll()
                self._ensure_started()
                self._loop_hook()

                readers, _, _ = select.select(
                    [self._control_channel, self._process.stdout], [], [], 1)

                for handle in readers:
                    if handle.fileno() == self._control_fd:
                        self._callbacks.input(handle.readline().strip(), song)
                    else:
                        value = self._read_from_process(handle)
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


class MPG123Player(BasePlayer):
    """Player Backend Using mpg123
    """

    def __init__(self, callbacks, control_channel):
        super(MPG123Player, self).__init__(callbacks, control_channel)
        self._cmd.extend(["-q", "-R", "--ignore-mime", "."])

    def _find_path(self):
        loc = which("mpg123")
        if not loc:
            raise PlayerUnusable("Unable to find mpg123")

        return loc

    def _load_track(self, song):
        if song.encoding != "mp3":
            raise UnsupportedEncoding("mpg123 only supports mp3 files")

        self._send_cmd("load {}".format(song.audio_url))

    def _post_start(self):
        # Only output play status in the player stdout
        self._send_cmd("silence")

    def _player_stopped(self, value):
        return value.startswith(b"@P") and value.decode("utf-8")[3] == "0"


class VLCPlayer(BasePlayer):

    POLL_INTERVAL = 3
    CHUNK_SIZE = 1024
    VOL_STEPS = 5

    def __init__(self, callbacks, control_channel):
        super(VLCPlayer, self).__init__(callbacks, control_channel)
        self._cmd.extend(["-I", "rc", "--advanced", "--rc-fake-tty", "-q"])
        self._last_poll = 0

    def _find_path(self):
        loc = which("vlc")
        if not loc:  # Mac OS X
            loc = which("VLC", path="/Applications/VLC.app/Contents/MacOS")

        if not loc:
            raise PlayerUnusable("Unable to find VLC")

        return loc

    def raise_volume(self):
        self._send_cmd("volup {}".format(self.VOL_STEPS))

    def lower_volume(self):
        self._send_cmd("voldown {}".format(self.VOL_STEPS))

    def _post_start(self):
        """Set stdout to non-blocking

        VLC does not always return a newline when reading status so in order to
        be lazy and still use the read API without caring about how much output
        there is we switch stdout to nonblocking mode and just read a large
        chunk of datin order to be lazy and still use the read API without
        caring about how much output there is we switch stdout to nonblocking
        mode and just read a large chunk of data.
        """
        flags = fcntl.fcntl(self._process.stdout, fcntl.F_GETFL)
        fcntl.fcntl(self._process.stdout, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    def _read_from_process(self, handle):
        return handle.read(self.CHUNK_SIZE).strip()

    def _load_track(self, song):
        self._send_cmd("add {}".format(song.audio_url))

    def _player_stopped(self, value):
        return "state stopped" in value.decode("utf-8")

    def _loop_hook(self):
        if (time.time() - self._last_poll) >= self.POLL_INTERVAL:
            self._send_cmd("status")
            self._last_poll = time.time()

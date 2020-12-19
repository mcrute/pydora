import os
import sys
import getpass
import subprocess


class TerminalPlatformUnsupported(Exception):
    """Platform-specific functionality is not supported

    Raised by code that can not be used to interact with the terminal on this
    platform.
    """

    pass


class Colors:
    def __wrap_with(raw_code):
        @staticmethod
        def inner(text, bold=False):
            code = raw_code
            if bold:
                code = "1;{}".format(code)
            return "\033[{}m{}\033[0m".format(code, text)

        return inner

    red = __wrap_with("31")
    green = __wrap_with("32")
    yellow = __wrap_with("33")
    blue = __wrap_with("34")
    magenta = __wrap_with("35")
    cyan = __wrap_with("36")
    white = __wrap_with("37")


class PosixEchoControl:
    """Posix Console Echo Control Driver

    Uses termios on POSIX compliant platforms to control console echo. Is not
    supported on Windows as termios is not available and will throw a
    TerminalPlatformUnsupported exception if contructed on Windows.
    """

    def __init__(self):
        try:
            import termios

            self.termios = termios
        except ImportError:
            raise TerminalPlatformUnsupported("POSIX not supported")

    def set_echo(self, enabled):
        handle = sys.stdin.fileno()
        if not os.isatty(handle):
            return

        attrs = self.termios.tcgetattr(handle)

        if enabled:
            attrs[3] |= self.termios.ECHO
        else:
            attrs[3] &= ~self.termios.ECHO

        self.termios.tcsetattr(handle, self.termios.TCSANOW, attrs)


class Win32EchoControl:
    """Windows Console Echo Control Driver

    This uses the console API from WinCon.h and ctypes to control console echo
    on Windows clients. It is not possible to construct this class on
    non-Windows systems, on those systems it will throw a
    TerminalPlatformUnsupported exception.
    """

    STD_INPUT_HANDLE = -10
    ENABLE_ECHO_INPUT = 0x4
    DISABLE_ECHO_INPUT = ~ENABLE_ECHO_INPUT

    def __init__(self):
        import ctypes

        if not hasattr(ctypes, "windll"):
            raise TerminalPlatformUnsupported("Windows not supported")

        from ctypes import wintypes

        self.ctypes = ctypes
        self.wintypes = wintypes
        self.kernel32 = ctypes.windll.kernel32

    def _GetStdHandle(self, handle):
        return self.kernel32.GetStdHandle(handle)

    def _GetConsoleMode(self, handle):
        mode = self.wintypes.DWORD()
        self.kernel32.GetConsoleMode(handle, self.ctypes.byref(mode))
        return mode.value

    def _SetConsoleMode(self, handle, value):
        self.kernel32.SetConsoleMode(handle, value)

    def set_echo(self, enabled):
        stdin = self._GetStdHandle(self.STD_INPUT_HANDLE)
        mode = self._GetConsoleMode(stdin)

        if enabled:
            self._SetConsoleMode(stdin, mode | self.ENABLE_ECHO_INPUT)
        else:
            self._SetConsoleMode(stdin, mode & self.DISABLE_ECHO_INPUT)


class Screen:
    def __init__(self):
        try:
            self._echo_driver = PosixEchoControl()
        except TerminalPlatformUnsupported:
            pass

        try:
            self._echo_driver = Win32EchoControl()
        except TerminalPlatformUnsupported:
            pass

        if not self._echo_driver:
            raise TerminalPlatformUnsupported("No supported terminal driver")

    def set_echo(self, enabled):
        self._echo_driver.set_echo(enabled)

    @staticmethod
    def clear():
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.flush()

    @staticmethod
    def print_error(msg):
        print(Colors.red(msg))

    @staticmethod
    def print_success(msg):
        print(Colors.green(msg))

    @staticmethod
    def get_string(prompt):
        while True:
            value = input(prompt).strip()

            if not value:
                print(Colors.red("Value Required!"))
            else:
                return value

    @staticmethod
    def get_password(prompt="Password: "):
        while True:
            value = getpass.getpass(prompt)

            if not value:
                print(Colors.red("Value Required!"))
            else:
                return value

    @staticmethod
    def get_integer(prompt):
        """Gather user input and convert it to an integer

        Will keep trying till the user enters an interger or until they ^C the
        program.
        """
        while True:
            try:
                return int(input(prompt).strip())
            except ValueError:
                print(Colors.red("Invalid Input!"))


def iterate_forever(func, *args, **kwargs):
    """Iterate over a finite iterator forever

    When the iterator is exhausted will call the function again to generate a
    new iterator and keep iterating.
    """
    output = func(*args, **kwargs)

    while True:
        try:
            playlist_item = next(output)
            playlist_item.prepare_playback()
            yield playlist_item
        except StopIteration:
            output = func(*args, **kwargs)


class SilentPopen(subprocess.Popen):
    """A Popen varient that dumps it's output and error"""

    def __init__(self, *args, **kwargs):
        self._dev_null = open(os.devnull, "w")
        kwargs["stdin"] = subprocess.PIPE
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = self._dev_null
        super().__init__(*args, **kwargs)

    def __del__(self):
        self._dev_null.close()
        super().__del__()

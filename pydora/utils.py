from __future__ import print_function

import os
import sys
import termios
import getpass
import subprocess


def input(prompt):
    try:
        return raw_input(prompt)
    except NameError:
        import builtins
        return builtins.input(prompt)


class Colors(object):

    def __wrap_with(code):
        @staticmethod
        def inner(text, bold=False):
            c = code
            if bold:
                c = "1;{}".format(c)
            return "\033[{}m{}\033[0m".format(c, text)
        return inner

    red = __wrap_with("31")
    green = __wrap_with("32")
    yellow = __wrap_with("33")
    blue = __wrap_with("34")
    magenta = __wrap_with("35")
    cyan = __wrap_with("36")
    white = __wrap_with("37")


class Screen(object):

    @staticmethod
    def set_echo(enabled):
        fd = sys.stdin.fileno()
        if not os.isatty(fd):
            return

        (iflag, oflag, cflag,
         lflag, ispeed, ospeed, cc) = termios.tcgetattr(fd)

        if enabled:
            lflag |= termios.ECHO
        else:
            lflag &= ~termios.ECHO

        termios.tcsetattr(fd, termios.TCSANOW,
                          [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])

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


def clear_screen():
    """Clear the terminal
    """
    sys.stdout.write("\x1b[2J\x1b[H")
    sys.stdout.flush()


def iterate_forever(func, *args, **kwargs):
    """Iterate over a finite iterator forever

    When the iterator is exhausted will call the function again to generate a
    new iterator and keep iterating.
    """
    output = func(*args, **kwargs)

    while True:
        try:
            yield next(output).prepare_playback()
        except StopIteration:
            output = func(*args, **kwargs)


class SilentPopen(subprocess.Popen):
    """A Popen varient that dumps it's output and error
    """

    def __init__(self, *args, **kwargs):
        self._dev_null = open(os.devnull, "w")
        kwargs["stdin"] = subprocess.PIPE
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = self._dev_null
        super(SilentPopen, self).__init__(*args, **kwargs)

    def __del__(self):
        self._dev_null.close()
        super(SilentPopen, self).__del__()

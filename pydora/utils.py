from __future__ import print_function

import sys
import termios


def input(prompt):
    try:
        return raw_input(prompt)
    except NameError:
        import builtins
        return builtins.input(prompt)


class Colors:

    def __wrap_with(code):
        @staticmethod
        def inner(text, bold=False):
            c = code
            if bold:
                c = u"1;{}".format(c)
            return u"\033[{}m{}\033[0m".format(c, text)
        return inner

    red = __wrap_with('31')
    green = __wrap_with('32')
    yellow = __wrap_with('33')
    blue = __wrap_with('34')
    magenta = __wrap_with('35')
    cyan = __wrap_with('36')
    white = __wrap_with('37')


class Screen:

    @staticmethod
    def set_echo(enabled):
        fd = sys.stdin.fileno()
        (iflag, oflag, cflag, lflag, ispeed, ospeed, cc) = \
            termios.tcgetattr(fd)

        if enabled:
            lflag |= termios.ECHO
        else:
            lflag &= ~termios.ECHO

        termios.tcsetattr(fd, termios.TCSANOW,
            [iflag, oflag, cflag, lflag, ispeed, ospeed, cc])

    @staticmethod
    def clear():
        sys.stdout.write('\x1b[2J\x1b[H')
        sys.stdout.flush()

    @staticmethod
    def print_error(msg):
        print(Colors.red(msg))

    @staticmethod
    def print_success(msg):
        print(Colors.green(msg))

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
                print(Colors.red('Invaid Input!'))


def clear_screen():
    """Clear the terminal
    """
    sys.stdout.write('\x1b[2J\x1b[H')
    sys.stdout.flush()

import json
import logging
import os
import signal
import sys
from contextlib import contextmanager


class IOHandler:
    def __init__(self, inp=sys.stdin, out=sys.stdout):
        self.inp = inp
        self.out = out

    def write_line(self, message):
        """Unbuffered printing to stdout."""

        self.out.write(message + "\n")
        self.out.flush()

    def read(self):
        """Iterate over all input lines (Generator)"""

        while True:
            try:
                yield self.read_line()
            except EOFError:
                return

    def read_line(self):
        """
        Interrupted respecting reader for stdin.

        Raises EOFError if the end of stream has been reached
        """

        try:
            line = self.inp.readline().strip()
        except KeyboardInterrupt:
            raise EOFError()

        # i3status sends EOF, or an empty line
        if not line:
            raise EOFError()
        return line


class StandaloneIO(IOHandler):
    """
    I/O handler for standalone usage of i3pystatus (w/o i3status)

    Writing works as usual, but reading will always return a empty JSON array,
    and the i3bar protocol header
    """

    refresh_modules = True

    n = -1
    proto = [
        {"version": 1, "click_events": True}, "[", "[]", ",[]",
    ]

    def __init__(self, click_events, modules, interval=1):
        super().__init__()
        self.interval = interval
        self.proto[0]['click_events'] = click_events
        self.proto[0] = json.dumps(self.proto[0])
        self.modules = modules

    def read(self):
        while True:
            received_signal = None
            try:
                received_signal = signal.sigtimedwait([signal.SIGUSR1], self.interval)
            except InterruptedError:
                logging.getLogger("i3pystatus").exception("Interrupted system call:")
            except KeyboardInterrupt:
                return

            if received_signal:
                if StandaloneIO.refresh_modules:
                    # refresh whole bar
                    for module in self.modules:
                        module.on_refresh()
                else:
                    # just send status line to i3bar immediately -> do nothing here

                    # set next signal action back to default
                    StandaloneIO.refresh_modules = True

            yield self.read_line()

    def read_line(self):
        self.n += 1

        return self.proto[min(self.n, len(self.proto) - 1)]

    @classmethod
    def refresh_statusline(cls):
        """
        Changes behavior of the next SIGUSR1 signal to just flushing current
        outputs of all modules and sends the signal.
        """
        cls.refresh_modules = False
        os.kill(os.getpid(), signal.SIGUSR1)


class JSONIO:
    def __init__(self, io, skiplines=2):
        self.io = io
        for i in range(skiplines):
            self.io.write_line(self.io.read_line())

    def read(self):
        """Iterate over all JSON input (Generator)"""

        for line in self.io.read():
            with self.parse_line(line) as j:
                yield j

    @contextmanager
    def parse_line(self, line):
        """Parse a single line of JSON and write modified JSON back."""

        prefix = ""
        # ignore comma at start of lines
        if line.startswith(","):
            line, prefix = line[1:], ","

        j = json.loads(line)
        yield j
        self.io.write_line(prefix + json.dumps(j))

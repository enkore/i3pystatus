import json
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

    n = -1
    proto = [
        {"version": 1, "click_events": True}, "[", "[]", ",[]",
    ]

    def __init__(self, click_events, interval=1):
        super().__init__()
        self.interval = interval
        self.proto[0]['click_events'] = click_events
        self.proto[0] = json.dumps(self.proto[0])

    def read(self):
        while True:
            try:
                signal.sigtimedwait([signal.SIGUSR1], self.interval)
            except InterruptedError:
                pass
            except KeyboardInterrupt:
                return

            yield self.read_line()

    def read_line(self):
        self.n += 1

        return self.proto[min(self.n, len(self.proto) - 1)]


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

import json
import signal
import sys
from contextlib import contextmanager
from threading import Condition
from threading import Thread


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

    refresh_cond = Condition()
    modules = []
    treshold_interval = 20.0

    n = -1
    proto = [
        {"version": 1, "click_events": True}, "[", "[]", ",[]",
    ]

    def __init__(self, click_events, modules, interval=1):
        """
        StandaloneIO instance must be created in main thread to set SIGUSR1
        signal handler.
        """

        super().__init__()
        self.interval = interval
        self.proto[0]['click_events'] = click_events
        self.proto[0] = json.dumps(self.proto[0])

        signal.signal(signal.SIGUSR1, StandaloneIO.refresh_signal_handler)
        StandaloneIO.modules = modules

    def read(self):
        StandaloneIO.compute_treshold_interval()
        StandaloneIO.refresh_cond.acquire()

        while True:
            try:
                StandaloneIO.refresh_cond.wait(timeout=self.interval)
            except KeyboardInterrupt:
                StandaloneIO.refresh_cond.release()
                return

            yield self.read_line()

    def read_line(self):
        self.n += 1

        return self.proto[min(self.n, len(self.proto) - 1)]

    @classmethod
    def compute_treshold_interval(cls):
        intervals = [m.interval for m in cls.modules if hasattr(m, "interval")]
        cls.treshold_interval = round(sum(intervals) / len(intervals))

    @classmethod
    def async_refresh(cls):
        cls.refresh_cond.acquire()
        cls.refresh_cond.notify()
        cls.refresh_cond.release()

    @staticmethod
    def refresh_signal_handler(signo, frame):
        if signo != signal.SIGUSR1:
            return

        threads = []
        for module in StandaloneIO.modules:
            if hasattr(module, "interval"):
                if module.interval > StandaloneIO.treshold_interval:
                    thread = Thread(target=module.run)
                    thread.start()
                else:
                    module.run()
            else:
                module.run()

        StandaloneIO.async_refresh()


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

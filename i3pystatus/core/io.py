import json
import signal
import sys

from contextlib import contextmanager
from threading import Condition
from threading import Thread
from i3pystatus.core.modules import IntervalModule


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
        {
            "version": 1,
            "click_events": True,
        }, "[", "[]", ",[]",
    ]

    def __init__(self, click_events, modules, keep_alive, interval=1):
        """
        StandaloneIO instance must be created in main thread to be able to set
        the SIGUSR1 signal handler.
        """

        super().__init__()
        self.interval = interval
        self.modules = modules

        self.proto[0]['click_events'] = click_events

        if keep_alive:
            self.proto[0].update(dict(stop_signal=signal.SIGUSR2,
                                      cont_signal=signal.SIGUSR2))
            signal.signal(signal.SIGUSR2, self.suspend_signal_handler)

        self.proto[0] = json.dumps(self.proto[0])

        self.refresh_cond = Condition()
        self.treshold_interval = 20.0

        self.stopped = False
        signal.signal(signal.SIGUSR1, self.refresh_signal_handler)

    def read(self):
        self.compute_treshold_interval()
        self.refresh_cond.acquire()

        while True:
            try:
                self.refresh_cond.wait(timeout=self.interval)
            except KeyboardInterrupt:
                self.refresh_cond.release()
                return

            yield self.read_line()

    def read_line(self):
        self.n += 1

        return self.proto[min(self.n, len(self.proto) - 1)]

    def compute_treshold_interval(self):
        """
        Current method is to compute average from all intervals.
        """

        intervals = [m.interval for m in self.modules if hasattr(m, "interval")]
        if len(intervals) > 0:
            self.treshold_interval = round(sum(intervals) / len(intervals))

    def async_refresh(self):
        """
        Calling this method will send the status line to i3bar immediately
        without waiting for timeout (1s by default).
        """

        self.refresh_cond.acquire()
        self.refresh_cond.notify()
        self.refresh_cond.release()

    def refresh_signal_handler(self, signo, frame):
        """
        This callback is called when SIGUSR1 signal is received.

        It updates outputs of all modules by calling their `run` method.

        Interval modules are updated in separate threads if their interval is
        above a certain treshold value.
        This treshold is computed by :func:`compute_treshold_interval` class
        method.
        The reasoning is that modules with larger intervals also usually take
        longer to refresh their output and that their output is not required in
        'real time'.
        This also prevents possible lag when updating all modules in a row.
        """

        if signo != signal.SIGUSR1:
            return

        for module in self.modules:
            if hasattr(module, "interval"):
                if module.interval > self.treshold_interval:
                    thread = Thread(target=module.run)
                    thread.start()
                else:
                    module.run()
            else:
                module.run()

        self.async_refresh()

    def suspend_signal_handler(self, signo, frame):
        """
        By default, i3bar sends SIGSTOP to all children when it is not visible (for example, the screen
        sleeps or you enter full screen mode). This stops the i3pystatus process and all threads within it.
        For some modules, this is not desirable. Thankfully, the i3bar protocol supports setting the "stop_signal"
        and "cont_signal" key/value pairs in the header to allow sending a custom signal when these events occur.

        Here we use SIGUSR2 for both "stop_signal" and "cont_signal" and maintain a toggle to determine whether
        we have just been stopped or continued. When we have been stopped, notify the IntervalModule managers
        that they should suspend any module that does not set the keep_alive flag to a truthy value, and when we
        have been continued, notify the IntervalModule managers that they can resume execution of all modules.
        """
        if signo != signal.SIGUSR2:
            return
        self.stopped = not self.stopped
        if self.stopped:
            [m.suspend() for m in IntervalModule.managers.values()]
        else:
            [m.resume() for m in IntervalModule.managers.values()]


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

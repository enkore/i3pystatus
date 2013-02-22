#!/usr/bin/env python

import sys
import json
from threading import Thread
import time
from contextlib import contextmanager

class Module:
    output = None
    position = 0

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

class AsyncModule(Module):
    def registered(self, status_handler):
        self.thread = Thread(target=self.mainloop)
        self.thread.daemon = True
        self.thread.start()

    def mainloop(self):
        """This is run in a separate daemon-thread"""

class IntervalModule(AsyncModule):
    interval = 5 # seconds

    def run(self):
        """Called every self.interval seconds"""

    def mainloop(self):
        while True:
            self.run()
            time.sleep(self.interval)

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
        """Interrupted respecting reader for stdin.

        Raises EOFError if the end of stream has been reached"""

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

    writing as usual, reading will always return a empty JSON array,
    and the i3bar protocol header
    """

    n = -1
    def __init__(self, interval=1):
        super().__init__()
        self.interval = interval

    def read(self):
        while True:
            yield self.read_line()
            time.sleep(self.interval)

    def read_line(self):
        self.n += 1

        if self.n == 0:
            return '{"version": 1}'
        elif self.n == 1:
            return "["
        else:
            return  ",[]"

class JSONIO:
    def __init__(self, io):
        self.io = io
        self.io.write_line(self.io.read_line())
        self.io.write_line(self.io.read_line())

    def read(self):
        """Iterate over all JSON input (Generator)"""

        for line in self.io.read():
            with self.parse_line(line) as j:
                yield j

    @contextmanager
    def parse_line(self, line):
        """Parse a single line of JSON and write modified JSON back.

        Usage is quite simple using the usual with-Syntax."""

        prefix = ""

        # ignore comma at start of lines
        if line.startswith(","):
            line, prefix = line[1:], ","

        j = json.loads(line)
        yield j
        self.io.write_line(prefix + json.dumps(j))

class i3pystatus:
    modules = []

    def __init__(self, standalone=False, interval=1, input_stream=sys.stdin):
        if standalone:
            self.io = StandaloneIO(interval)
        else:
            self.io = IOHandler(input_stream)

    def register(self, module, position=0):
        """Register a new module."""

        self.modules.append(module)
        module.position = position
        module.registered(self)

    def run(self):
        for j in JSONIO(self.io).read():
            for module in self.modules:
                j.insert(module.position, module.output)

I3statusHandler = i3pystatus

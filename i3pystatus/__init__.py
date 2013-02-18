#!/usr/bin/env python

import sys
import json
import urllib.request, urllib.error, urllib.parse
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
            line = self.inp.readline().decode("utf-8").strip()
        except KeyboardInterrupt:
            raise EOFError()

        # i3status sends EOF, or an empty line
        if not line:
            raise EOFError()
        return line

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

class I3statusHandler:
    modules = []

    def __init__(self, fd=None):
        if fd is None:
            fd = sys.stdin

        self.io = JSONIO(IOHandler(fd))

    def register(self, module, position=0):
        """Register a new module."""

        self.modules.append(module)
        module.position = position
        module.registered(self)

    def run(self):
        for j in self.io.read():
            for module in self.modules:
                j.insert(module.position, module.output)

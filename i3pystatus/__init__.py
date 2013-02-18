#!/usr/bin/env python

import sys
import json
import urllib.request, urllib.error, urllib.parse
from threading import Thread
import time
from contextlib import contextmanager

class Module:
    output = None

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

    def write(self, message):
        """Unbuffered printing to stdout."""

        self.out.write(message + "\n")
        self.out.flush()

    def read(self):
        """Interrupted respecting reader for stdin."""

        # try reading a line, removing any extra whitespace
        try:
            line = self.inp.readline().decode("utf-8").strip()
            # i3status sends EOF, or an empty line
            if not line:
                sys.exit(3)
            return line
        # exit on ctrl-c
        except KeyboardInterrupt:
            sys.exit()

class JSONIO:
    def __init__(self, io):
        self.io = io
        self.io.write(self.io.read())
        self.io.write(self.io.read())

    def read(self):
        while True:
            with self.read_line() as j:
                yield j

    @contextmanager
    def read_line(self):
        line, prefix = self.io.read(), ""

        # ignore comma at start of lines
        if line.startswith(","):
            line, prefix = line[1:], ","

        j = json.loads(line)
        yield j
        self.io.write(prefix + json.dumps(j))

class I3statusHandler:
    modules = []

    def __init__(self, fd=None):
        if fd is None:
            fd = sys.stdin

        self.io = JSONIO(IOHandler(fd))

    def register(self, module):
        """Register a new module."""

        self.modules.append(module)
        module.registered(self)

    def run(self):
        for j in  self.io.read():
            for module in self.modules:
                j.insert(0, module.output)

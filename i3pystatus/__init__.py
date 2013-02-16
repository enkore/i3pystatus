#!/usr/bin/env python

import sys
import json
import urllib.request, urllib.error, urllib.parse
from threading import Thread
import time

class BaseModule:
    output = None

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def tick(self):
        """Called once per tick"""

class Module(BaseModule):
    pass

class AsyncModule(BaseModule):
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

class I3statusHandler:
    modules = []
    fd = sys.stdin

    def __init__(self):
        pass

    def register(self, module):
        """Register a new module."""

        self.modules.append(module)
        module.registered(self)

    def print_line(self, message):
        """Unbuffered printing to stdout."""

        sys.stdout.write(message + "\n")
        sys.stdout.flush()

    def read_line(self):
        """Interrupted respecting reader for stdin."""

        # try reading a line, removing any extra whitespace
        try:
            line = self.fd.readline().decode("utf-8").strip()
            # i3status sends EOF, or an empty line
            if not line:
                sys.exit(3)
            return line
        # exit on ctrl-c
        except KeyboardInterrupt:
            sys.exit()

    def run(self):
        self.print_line(self.read_line())
        self.print_line(self.read_line())

        while True:
            line, prefix = self.read_line(), ""

            # ignore comma at start of lines
            if line.startswith(","):
                line, prefix = line[1:], ","

            j = json.loads(line)

            for module in self.modules:
                module.tick()

                output = module.output

                if output:
                    j.insert(0, output)

            # and echo back new encoded json
            self.print_line(prefix+json.dumps(j))

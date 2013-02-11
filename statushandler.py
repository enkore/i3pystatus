#!/usr/bin/env python

import sys
import json
import urllib.request, urllib.error, urllib.parse

class Module(object):
    output = None
    async = False

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def tick(self):
        """Only called if self.async == False. Called once per tick"""

class I3statusHandler(object):
    modules = []

    def __init__(self):
        pass

    def register_module(self, module):
        """Register a new module."""

        # check if module implemented the 
        # correct functions
        #if not hasattr(module, 'output'):
        #    raise Exception("Module %s does not implement \
        #        all the needed functions!".format(module))

        self.modules.append(module)

    def print_line(self, message):
        """Unbuffered printing to stdout."""

        sys.stdout.write(message + '\n')
        sys.stdout.flush()

    def read_line(self):
        """Interrupted respecting reader for stdin."""

        # try reading a line, removing any extra whitespace
        try:
            line = sys.stdin.readline().strip()
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
            line, prefix = self.read_line(), ''

            # ignore comma at start of lines
            if line.startswith(','):
                line, prefix = line[1:], ','

            j = [] #json.loads(line)

            for module in self.modules:
                if not module.async:
                    module.tick()

                output = module.output

                if output:
                    j.insert(0, output)

            # and echo back new encoded json
            self.print_line(prefix+json.dumps(j))


def has_internet_connection():
    try:
        response=urllib2.urlopen('http://173.194.69.94',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False

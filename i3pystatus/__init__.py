#!/usr/bin/env python

import sys
import json
from threading import Thread
import time
from contextlib import contextmanager
import types
import inspect

class ConfigurationError(Exception):
    def __init__(self, module, key=None, missing=None, ambigious_classes=None, invalid=False):
        message = "Module '{0}'".format(module)
        if key is not None:
            message += ": invalid option '{0}'".format(key)
        if missing is not None:
            message += ": missing required options: {0}".format(missing)
        if ambigious_classes is not None:
            message += ": ambigious module specification, found multiple classes: {0}".format(ambigious_classes)
        if invalid:
            message += ": no class found"

        super().__init__(message)

class Module:
    output = None
    position = 0
    settings = tuple()
    required = tuple()

    def __init__(self, *args, **kwargs):
        required = set()
        self.required = set(self.required)

        if len(args) == 1 and not len(kwargs):
            # User can also pass in a dict for their settings
            # Note: you could do that anyway, with the ** syntax
            # Note2: just for backwards compatibility
            kwargs = args[0]

        for key, value in kwargs.items():
            if key in self.settings:
                setattr(self, key, value)
                required.add(key)
            else:
                raise ConfigurationError(type(self).__name__, key=key)

        required &= set(self.required)
        if len(required) != len(self.required):
            raise ConfigurationError(type(self).__name__, missing=self.required-required)

        self.init()

    def init(self):
        """Convenience method which is called after all settings are set

        In case you don't want to type that super()…blabla :-)"""

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

    @staticmethod
    def _check_class(obj):
        return inspect.isclass(obj) and issubclass(obj, Module) and obj not in [Module, IntervalModule, AsyncModule]

    def register(self, module, position=0, *args, **kwargs):
        """Register a new module."""

        if isinstance(module, types.ModuleType):
            # Okay, we got a module, let's find the class
            # and create an instance

            # Neat trick: [(x,y),(u,v)] becomes [(x,u),(y,v)]
            names, classes = zip(*inspect.getmembers(module, self._check_class))

            if len(classes) > 1:
                # If there are multiple Module clases bundled in one module,
                # well, we can't decide for the user.
                raise ConfigurationError(module.__name__, ambigious_classes=classes)
            elif not classes:
                raise ConfigurationError(module.__name__, invalid=True)

            if not isinstance(position, int) and not args:
                # Small quirks:
                # If the user does this: register(modsde, mdesettings) with mdesettings
                # being a dict Python will put mdesettings into the position argument
                # , and not into *args. Let's fix that.
                # If she uses keyword arguments, everything is fine right from the beginning :-)
                args = (position,)
                position = 0

            module = classes[0](*args, **kwargs)

        self.modules.append(module)
        module.position = position
        module.registered(self)

    def run(self):
        for j in JSONIO(self.io).read():
            for module in self.modules:
                j.insert(module.position, module.output)
I3statusHandler = i3pystatus

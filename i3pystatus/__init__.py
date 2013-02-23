#!/usr/bin/env python

import sys
import json
from threading import Thread
import time
from contextlib import contextmanager
import types
import inspect
import functools
import collections

__all__ = [
    "SettingsBase", "ClassFinder", "ModuleFinder",
    "ConfigError", "ConfigKeyError", "ConfigMissingError", "ConfigAmbigiousClassesError", "ConfigInvalidModuleError",
    "Module", "AsyncModule", "IntervalModule",
    "i3pystatus", "I3statusHandler",
]

class ConfigError(Exception):
    """ABC for configuration exceptions"""
    def __init__(self, module, *args, **kwargs):
        message = "Module '{0}': {1}".format(module, self.format(*args, **kwargs))

        super().__init__(message)

class ConfigKeyError(ConfigError, KeyError):
    def format(self, key):
        return "invalid option '{0}'".format(key)

class ConfigMissingError(ConfigError):
    def format(self, missing):
        return "missing required options: {0}".format(missing)
        super().__init__(module)

class ConfigAmbigiousClassesError(ConfigError):
    def format(self, ambigious_classes):
        return "ambigious module specification, found multiple classes: {0}".format(ambigious_classes)

class ConfigInvalidModuleError(ConfigError):
    def format(self):
        return "no class found"

class KeyConstraintDict(collections.UserDict):
    class MissingKeys(Exception):
        def __init__(self, keys):
            self.keys = keys

    def __init__(self, valid_keys, required_keys):
        super().__init__()

        self.valid_keys = valid_keys
        self.required_keys = set(required_keys)
        self.seen_keys = set()

    def __setitem__(self, key, value):
        if key in self.valid_keys:
            self.seen_keys.add(key)
            self.data[key] = value
        else:
            raise KeyError(key)

    def missing(self):
        return self.required_keys - (self.seen_keys & self.required_keys)

    def __iter__(self):
        if self.missing():
            raise self.MissingKeys(self.missing())

        return self.data.__iter__()

class SettingsBase:
    """
    Support class for providing a nice and flexible settings interface

    Classes inherit from this class and define what settings they provide and
    which are required.

    The constructor is either passed a dictionary containing these settings, or
    keyword arguments specifying the same.

    Settings are stored as attributes of self
    """

    settings = tuple()
    """settings should be tuple containing two types of elements:
    * bare strings, which must be valid identifiers.
    * two-tuples, the first element being a identifier (as above) and the second
    a docstring for the particular setting"""

    required = tuple()
    """required can list settings which are required"""

    def __init__(self, *args, **kwargs):
        def flatten_setting(setting):
            return setting[0] if isinstance(setting, tuple) else setting
        def flatten_settings(settings):
            return tuple(flatten_setting(setting) for setting in settings)

        def get_argument_dict(args, kwargs):
            if len(args) == 1 and not kwargs:
                # User can also pass in a dict for their settings
                # Note: you could do that anyway, with the ** syntax
                return args[0]
            return kwargs

        self.settings = flatten_settings(self.settings)

        sm = KeyConstraintDict(self.settings, self.required)
        settings_source = get_argument_dict(args, kwargs)

        try:
            sm.update(settings_source)
        except KeyError as exc:
           raise ConfigKeyError(type(self).__name__, key=exc.args[0]) from exc

        try:
            self.__dict__.update(sm)
        except KeyConstraintDict.MissingKeys as exc:
            raise ConfigMissingError(type(self).__name__, missing=exc.keys) from exc

        self.__name__ = "{}.{}".format(self.__module__, self.__class__.__name__)

        self.init()

    def init(self):
        """Convenience method which is called after all settings are set

        In case you don't want to type that super()…blabla :-)"""

class Module(SettingsBase):
    output = None
    position = 0

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def inject(self, json):
        if self.output:
            if "name" not in self.output:
                self.output["name"] = self.__name__
            json.insert(self.position, self.output)

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

class ClassFinder:
    """Support class to find classes of specific bases in a module"""

    def __init__(self, baseclass, exclude=[]):
        self.baseclass = baseclass
        self.exclude = exclude

    def predicate(self, obj):
        return inspect.isclass(obj) and issubclass(obj, self.baseclass) and obj not in self.exclude

    def search_module(self, module):
        # Neat trick: [(x,y),(u,v)] becomes [(x,u),(y,v)]
        return list(zip(*inspect.getmembers(module, self.predicate)))[1]

    def get_class(self, module):
        classes = self.search_module(module)

        if len(classes) > 1:
            # If there are multiple Module clases bundled in one module,
            # well, we can't decide for the user.
            raise ConfigAmbigiousClassesError(module.__name__, classes)
        elif not classes:
            raise ConfigInvalidModuleError(module.__name__)

        return classes[0]

    def instanciate_class_from_module(self, module, *args, **kwargs):
        return self.get_class(module)(*args, **kwargs)

ModuleFinder = functools.partial(ClassFinder, baseclass=Module, exclude=[Module, IntervalModule, AsyncModule])

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

    Writing works as usual, but reading will always return a empty JSON array,
    and the i3bar protocol header
    """

    n = -1
    proto = (
        '{"version":1}',
        "[",
        "[]",
        ",[]",
    )

    def __init__(self, interval=1):
        super().__init__()
        self.interval = interval

    def read(self):
        while True:
            try:
                time.sleep(self.interval)
            except KeyboardInterrupt:
                return
            yield self.read_line()

    def read_line(self):
        self.n += 1

        return self.proto[min(self.n, len(self.proto)-1)]

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
        """
        Parse a single line of JSON and write modified JSON back.

        Usage is quite simple using the usual with-Syntax.
        """

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

        self.finder = ModuleFinder()

    def get_instance_for_module(self, module, position, args, kwargs):
        if isinstance(module, types.ModuleType):
            if not isinstance(position, int) and not args:
                # If the user does this: register(modsde, mdesettings) with mdesettings
                # being a dict Python will put mdesettings into the position argument
                # , and not into *args. Let's fix that.
                # If she uses keyword arguments, everything is fine :-)
                args = (position,)
                position = 0

            module = self.finder.instanciate_class_from_module(module, *args, **kwargs)
        elif args or kwargs:
            raise ValueError("Additional arguments are invalid if 'module' is already an object")

        return (module, position)

    def register(self, module, position=0, *args, **kwargs):
        """Register a new module."""

        module, position = self.get_instance_for_module(module, position, args, kwargs)

        self.modules.append(module)
        module.position = position
        module.registered(self)

    def run(self):
        for j in JSONIO(self.io).read():
            for module in self.modules:
                module.inject(j)
I3statusHandler = i3pystatus

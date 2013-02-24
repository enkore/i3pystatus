#!/usr/bin/env python

import sys
import types
from threading import Thread
import time
import functools
import collections

from .core import io
from .core.util import *

__all__ = [
    "SettingsBase",
    "ClassFinder", "ModuleFinder",
    "Module", "AsyncModule", "IntervalModule",
    "i3pystatus", "I3statusHandler",
]

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

class i3pystatus:
    modules = []

    def __init__(self, standalone=False, interval=1, input_stream=sys.stdin):
        if standalone:
            self.io = core.io.StandaloneIO(interval)
        else:
            self.io = core.io.IOHandler(input_stream)

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

        if not module: # One can pass in False or None, if he wishes to temporarily disable a module
            return

        module, position = self.get_instance_for_module(module, position, args, kwargs)

        self.modules.append(module)
        module.position = position
        module.registered(self)

    def run(self):
        for j in core.io.JSONIO(self.io).read():
            for module in self.modules:
                module.inject(j)
I3statusHandler = i3pystatus

ModuleFinder = functools.partial(ClassFinder, baseclass=Module, exclude=[Module, IntervalModule, AsyncModule])

#!/usr/bin/env python

import sys
from threading import Thread
import time
import functools

from .core import io
from .core.util import *

__all__ = [
    "SettingsBase",
    "ClassFinder",
    "Module", "AsyncModule", "IntervalModule",
    "i3pystatus", "I3statusHandler",
]

class Module(SettingsBase):
    output = None

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def inject(self, json):
        if self.output:
            if "name" not in self.output:
                self.output["name"] = self.__name__
            json.insert(0, self.output)

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
    def __init__(self, standalone=False, interval=1, input_stream=sys.stdin):
        if standalone:
            self.io = core.io.StandaloneIO(interval)
        else:
            self.io = core.io.IOHandler(input_stream)

        self.finder = ClassFinder(Module)
        self.modules = ModuleList(self)

    def register(self, module, *args, **kwargs):
        """Register a new module."""

        if module:
            self.modules.append(self.finder.instanciate_class_from_module(module, *args, **kwargs))

    def run(self):
        for j in core.io.JSONIO(self.io).read():
            for module in self.modules:
                module.inject(j)
I3statusHandler = i3pystatus

#!/usr/bin/env python

import sys

from .core import io
from .core.util import *
from .core.modules import *

__all__ = [
    "SettingsBase",
    "Module", "AsyncModule", "IntervalModule",
    "Status", "I3statusHandler",
]

class Status:
    def __init__(self, standalone=False, interval=1, input_stream=sys.stdin):
        if standalone:
            self.io = core.io.StandaloneIO(interval)
        else:
            self.io = core.io.IOHandler(input_stream)

        self.modules = ModuleList(self, Module)

    def register(self, module, *args, **kwargs):
        """Register a new module."""

        if module:
            self.modules.append(module, *args, **kwargs)

    def run(self):
        for j in core.io.JSONIO(self.io).read():
            for module in self.modules:
                module.inject(j)
I3statusHandler = Status

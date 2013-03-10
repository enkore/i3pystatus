#!/usr/bin/env python

import sys
import threading
import os

from .core import util, io
from .core.modules import Module, AsyncModule, IntervalModule, START_HOOKS
from .core.settings import SettingsBase
from .core.config import ConfigFinder
from .core.render import render_json

__all__ = [
    "SettingsBase",
    "Module", "AsyncModule", "IntervalModule",
    "Status", "I3statusHandler",
]

class Status:
    def __init__(self, standalone=False, interval=1, input_stream=sys.stdin):
        self.standalone = standalone
        if standalone:
            self.io = io.StandaloneIO(interval)
            self.ce_thread = threading.Thread(target=self.run_command_endpoint)
            self.ce_thread.daemon = True
            self.ce_thread.start()
        else:
            self.io = io.IOHandler(input_stream)

        self.modules = util.ModuleList(self, Module)

    def register(self, module, *args, **kwargs):
        """Register a new module."""

        if module:
            self.modules.append(module, *args, **kwargs)

    def run_command_endpoint(self):
        for command in io.JSONIO(io=io.IOHandler(sys.stdin, open(os.devnull,"w")), skiplines=1).read():
            if command["command"] == "block_clicked":
                module = self.modules.get_by_id(command["instance"])
                if module:
                    module.on_click(command["button"])

    def call_start_hooks(self):
        for hook in START_HOOKS:
            hook()

    def run(self):
        self.call_start_hooks()
        for j in io.JSONIO(self.io).read():
            for module in self.modules:
                module.inject(j)
I3statusHandler = Status

def run_config():
    ConfigFinder().run_config()

def test_setup():
    import i3pystatus
    class TestStatus(Status):
        def run(self):
            self.call_start_hooks()
            for module in self.modules:

                sys.stdout.write("{module}: ".format(module=module.__name__))
                sys.stdout.flush()
                module.run()
                output = module.output or {"full_text": "(no output)"}
                print(render_json(output))

    i3pystatus.Status = TestStatus

def test_config():
    test_setup()
    cf = ConfigFinder()
    print("Using configuration file {file}".format(file=cf.get_config_path()[1]))
    print("Output, would be displayed right to left in i3bar")
    cf.run_config()

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        test_config()
    else:
        run_config()

#!/usr/bin/env python

import sys

from .core import Status
from .core.modules import Module, AsyncModule, IntervalModule
from .core.settings import SettingsBase
from .core.config import ConfigFinder
from .core.render import render_json

__all__ = [
    "SettingsBase",
    "Module", "AsyncModule", "IntervalModule",
    "Status",
]

def run_config():
    ConfigFinder().run_config()

def test_config():
    def test_setup():
        """This is a wrapped method so no one ever tries to use it outside of this"""
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
    test_setup()
    cf = ConfigFinder()
    print("Using configuration file {file}".format(file=cf.get_config_path()[1]))
    print("Output, would be displayed right to left in i3bar")
    cf.run_config()
    sys.exit(0)

def main():
    if len(sys.argv) == 2 and sys.argv[1] == "test":
        test_config()
    else:
        run_config()

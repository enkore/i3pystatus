
import sys
import threading
import os

from . import io, util
from .modules import Module, START_HOOKS

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

import sys
import os
from threading import Thread
from i3pystatus.core.exceptions import ConfigError

from i3pystatus.core.imputil import ClassFinder
from i3pystatus.core import io, util
from i3pystatus.core.modules import Module


class CommandEndpoint:
    """
    Endpoint for i3bar click events: http://i3wm.org/docs/i3bar-protocol.html#_click_events

    :param modules: dict-like object with item access semantics via .get()
    :param io_handler_factory: function creating a file-like object returning a JSON generator on .read()
    """

    def __init__(self, modules, io_handler_factory):
        self.modules = modules
        self.io_handler_factory = io_handler_factory
        self.thread = Thread(target=self._command_endpoint)
        self.thread.daemon = True

    def start(self):
        """Starts the background thread"""
        self.thread.start()

    def _command_endpoint(self):
        for command in self.io_handler_factory().read():
            target_module = self.modules.get(command["instance"])
            if target_module:
                target_module.on_click(command["button"])


class Status:
    """
    The main class used for registering modules and managing I/O

    :param standalone: Whether i3pystatus should read i3status-compatible input from `input_stream`
    :param interval: Update interval in seconds
    :param input_stream: A file-like object that provides the input stream, if `standalone` is False.
    """

    def __init__(self, standalone=False, interval=1, input_stream=sys.stdin, reversed_register=True):
        self.modules = util.ModuleList(self, ClassFinder(Module), reverse=reversed_register)
        self.standalone = standalone
        if standalone:
            self.io = io.StandaloneIO(interval)
            self.command_endpoint = CommandEndpoint(
                self.modules,
                lambda: io.JSONIO(io=io.IOHandler(sys.stdin, open(os.devnull, "w")), skiplines=1))
        else:
            self.io = io.IOHandler(input_stream)

    def register(self, module, *args, **kwargs):
        """Register a new module."""
        from i3pystatus.text import Text

        if not module:
            return

        try:
            return self.modules.append(module, *args, **kwargs)
        except ImportError as import_error:
            if import_error.name and not import_error.path and isinstance(module, str):
                # This is a package/module not found exception raised by importing a module on-the-fly
                return self.modules.append(Text(
                    color="#FF0000",
                    text="{i3py_mod}: Missing Python module '{missing_module}'".format(
                        i3py_mod=module,
                        missing_module=import_error.name)))
            else:
                raise import_error
        except ConfigError as configuration_error:
            return self.modules.append(Text(
                color="#FF0000",
                text=configuration_error.message))

    def run(self):
        self.command_endpoint.start()
        for j in io.JSONIO(self.io).read():
            for module in self.modules:
                module.inject(j)

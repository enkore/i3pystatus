import os
import signal
import sys
from threading import Thread

from i3pystatus.core import io
from i3pystatus.core import util
from i3pystatus.core.exceptions import ConfigError
from i3pystatus.core.imputil import ClassFinder
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
            if target_module and target_module.on_click(command["button"]):
                target_module.on_refresh()
                io.StandaloneIO.register_click_event()


class Status:
    """
    The main class used for registering modules and managing I/O

    :param standalone: Whether i3pystatus should read i3status-compatible input from `input_stream`
    :param interval: Update interval in seconds
    :param input_stream: A file-like object that provides the input stream, if `standalone` is False.
    :param click_events: Enable click events
    """

    def __init__(self, standalone=False, interval=1, input_stream=sys.stdin, click_events=True):
        self.modules = util.ModuleList(self, ClassFinder(Module))
        self.standalone = standalone
        self.click_events = click_events
        if standalone:
            def no_op(signum, stack):
                return
            signal.signal(signal.SIGUSR1, no_op)

            self.io = io.StandaloneIO(self.click_events, self.modules, interval)
            if self.click_events:
                self.command_endpoint = CommandEndpoint(
                    self.modules,
                    lambda: io.JSONIO(io=io.IOHandler(sys.stdin, open(os.devnull, "w")), skiplines=1))
        else:
            signal.signal(signal.SIGUSR1, signal.SIG_IGN)
            self.io = io.IOHandler(input_stream)

    def register(self, module, *args, **kwargs):
        """
        Register a new module.

        :param module: Either a string module name, or a module class,
                       or a module instance (in which case args and kwargs are
                       invalid).
        :param kwargs: Settings for the module.
        :returns: module instance
        """
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
        """
        Run main loop.
        """
        if self.click_events:
            self.command_endpoint.start()
        for j in io.JSONIO(self.io).read():
            for module in self.modules:
                module.inject(j)

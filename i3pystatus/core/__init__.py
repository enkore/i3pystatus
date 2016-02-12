import logging
import os
import sys
from threading import Thread

from i3pystatus.core import io, util
from i3pystatus.core.exceptions import ConfigError
from i3pystatus.core.imputil import ClassFinder
from i3pystatus.core.modules import Module


class CommandEndpoint:
    """
    Endpoint for i3bar click events: http://i3wm.org/docs/i3bar-protocol.html#_click_events

    :param modules: dict-like object with item access semantics via .get()
    :param io_handler_factory: function creating a file-like object returning a JSON generator on .read()
    """

    def __init__(self, modules, io_handler_factory, io):
        self.modules = modules
        self.io_handler_factory = io_handler_factory
        self.io = io
        self.thread = Thread(target=self._command_endpoint)
        self.thread.daemon = True

    def start(self):
        """Starts the background thread"""
        self.thread.start()

    def _command_endpoint(self):
        for command in self.io_handler_factory().read():
            target_module = self.modules.get(command["instance"])
            if target_module and target_module.on_click(command["button"]):
                target_module.run()
                self.io.async_refresh()


class Status:
    """
    The main class used for registering modules and managing I/O

    :param bool standalone: Whether i3pystatus should read i3status-compatible input from `input_stream`.
    :param int interval: Update interval in seconds.
    :param input_stream: A file-like object that provides the input stream, if `standalone` is False.
    :param bool click_events: Enable click events, if `standalone` is True.
    :param str logfile: Path to log file that will be used by i3pystatus.
    :param tuple internet_check: Address of server that will be used to check for internet connection by :py:class:`.internet`.
    """

    def __init__(self, standalone=True, click_events=True, interval=1,
                 input_stream=None, logfile=None, internet_check=None):
        self.standalone = standalone
        self.click_events = standalone and click_events
        input_stream = input_stream or sys.stdin
        if logfile:
            logger = logging.getLogger("i3pystatus")
            for handler in logger.handlers:
                logger.removeHandler(handler)
            handler = logging.FileHandler(logfile, delay=True)
            logger.addHandler(handler)
            logger.setLevel(logging.CRITICAL)
        if internet_check:
            util.internet.address = internet_check

        self.modules = util.ModuleList(self, ClassFinder(Module))
        if self.standalone:
            self.io = io.StandaloneIO(self.click_events, self.modules, interval)
            if self.click_events:
                self.command_endpoint = CommandEndpoint(
                    self.modules,
                    lambda: io.JSONIO(io=io.IOHandler(sys.stdin, open(os.devnull, "w")), skiplines=1),
                    self.io)
        else:
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

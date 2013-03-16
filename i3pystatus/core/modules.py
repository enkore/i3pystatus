
import time

from .settings import SettingsBase
from .threading import Manager
from .util import convert_position

__all__ = [
    "Module", "AsyncModule", "IntervalModule",
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
            self.output["instance"] = str(id(self))
            json.insert(convert_position(self.position, json), self.output)

    def on_click(self, button):
        if button == 1: # Left mouse button
            self.on_leftclick()
        elif button == 3: # Right mouse button
            self.on_rightclick()

    def move(self, position):
        self.position = position

    def on_leftclick(self):
        pass

    def on_rightclick(self):
        pass

    def __repr__(self):
        return self.__class__.__name__

class IntervalModule(Module):
    interval = 5 # seconds
    managers = {}

    def registered(self, status_handler):
        if self.interval in IntervalModule.managers:
            IntervalModule.managers[self.interval].append(self)
        else:
            am = Manager(self.interval)
            am.append(self)
            IntervalModule.managers[self.interval] = am

    @classmethod
    def _start(cls):
        for manager in cls.managers.values():
            manager.start()

    def __call__(self):
        self.run()

    def run(self):
        """Called approximately every self.interval seconds

        Do not rely on this being called from the same thread at all times.
        If you need to always have the same thread context, subclass AsyncModule."""

START_HOOKS = (
    IntervalModule._start,
)

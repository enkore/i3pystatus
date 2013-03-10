from threading import Thread
import time

from .settings import SettingsBase
from .threads import AutomagicManager

__all__ = [
    "Module", "AsyncModule", "IntervalModule",
]

class Module(SettingsBase):
    output = None

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def inject(self, json):
        if self.output:
            if "name" not in self.output:
                self.output["name"] = self.__name__
            self.output["instance"] = str(id(self))
            json.insert(0, self.output)

    def on_click(self, button):
        if button == 1: # Left mouse button
            self.on_leftclick()
        elif button == 3: # Right mouse button
            self.on_rightclick()

    def on_leftclick(self):
        pass

    def on_rightclick(self):
        pass

    def __repr__(self):
        return self.__class__.__name__

class AsyncModule(Module):
    def registered(self, status_handler):
        self.thread = Thread(target=self.mainloop)
        self.thread.daemon = True
        self.thread.start()

    def mainloop(self):
        """This is run in a separate daemon-thread"""

class IntervalModule(Module):
    interval = 5 # seconds
    managers = {}

    def registered(self, status_handler):
        if self.interval in IntervalModule.managers:
            IntervalModule.managers[self.interval].append(self)
        else:
            am = AutomagicManager(self.interval)
            am.append(self)
            IntervalModule.managers[self.interval] = am

    def __call__(self):
        self.run()

    def run(self):
        """Called approximately every self.interval seconds

        Do not rely on this being called from the same thread at all times.
        If you need to always have the same thread context, subclass AsyncModule."""

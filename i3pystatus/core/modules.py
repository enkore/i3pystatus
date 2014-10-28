from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.threading import Manager
from i3pystatus.core.util import convert_position


class Module(SettingsBase):
    output = None
    position = 0
    
    settings = (
        ("on_lclick","callback when left clicking"),
        ("on_rclick","callback when left clicking"),
        )

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def inject(self, json):
        if self.output:
            if "name" not in self.output:
                self.output["name"] = self.__name__
            self.output["instance"] = str(id(self))
            if (self.output.get("color", "") or "").lower() == "#ffffff":
                del self.output["color"]
            json.insert(convert_position(self.position, json), self.output)

    def run(self):
        pass

    def on_click(self, button):
        if button == 1:  # Left mouse button
            if self.on_lclick:
                self.on_lclick.run(self)
            else:
                self.on_leftclick()
        elif button == 3:  # Right mouse button
            if self.on_rclick:
                self.on_rclick.run(self)
            else:
                self.on_rightclick()
        elif button == 4: # mouse wheel up
            self.on_upscroll()
        elif button == 5: # mouse wheel down
            self.on_downscroll()

    def move(self, position):
        self.position = position
        return self

    def on_leftclick(self):
        pass

    def on_rightclick(self):
        pass

    def on_upscroll(self):
        pass

    def on_downscroll(self):
        pass

class IntervalModuleMeta(type):
    """Add interval setting to `settings` attribute if it does not exist."""

    def __init__(cls, name, bases, namespace):
        super(IntervalModuleMeta, cls).__init__(name, bases, namespace)
        if not hasattr(cls, 'settings'):
            cls.settings = tuple()
        # if 'interval' not in SettingsBase.flatten_settings(cls.settings):
        #     cls.settings += ('interval', )


class IntervalModule(Module, metaclass=IntervalModuleMeta):
    interval = 5  # seconds
    managers = {}

    def registered(self, status_handler):
        if self.interval in IntervalModule.managers:
            IntervalModule.managers[self.interval].append(self)
        else:
            am = Manager(self.interval)
            am.append(self)
            IntervalModule.managers[self.interval] = am
            am.start()

    def __call__(self):
        self.run()

    def run(self):
        """Called approximately every self.interval seconds

        Do not rely on this being called from the same thread at all times.
        If you need to always have the same thread context, subclass AsyncModule."""

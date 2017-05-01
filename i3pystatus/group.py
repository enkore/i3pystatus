from i3pystatus import IntervalModule, Status, Module
from i3pystatus.core import util
from i3pystatus.core.imputil import ClassFinder


class Group(Module, Status):
    """
    Module for grouping modules together
    Cycles trough groups by means of scrolling

    .. code-block:: python

        group = Group()
        group.register("network",
            interface="eth0",
            divisor=1024,
            start_color='white',
            format_up="{bytes_recv}K / {bytes_sent}K"
        )
        group.register("network",
            interface="eth0",
            color_up='#FFFFFF',
            format_up="{v4}"
        )
        status.register(group)

    """
    on_upscroll = ['cycle_module', 1]
    on_downscroll = ['cycle_module', -1]

    def __init__(self, *args, **kwargs):
        Module.__init__(self, *args, **kwargs)
        self.modules = util.ModuleList(self, ClassFinder(Module))
        self.active = 0
        self.__name__ = 'Group'

    def get_active_module(self):
        if self.active > len(self.modules):
            return
        return self.modules[self.active]

    def run(self):
        activemodule = self.get_active_module()
        if not activemodule:
            return
        self.output = activemodule.output

    def register(self, *args, **kwargs):
        module = Status.register(self, *args, **kwargs)
        if module:
            module.on_change = self.run
        return module

    def cycle_module(self, increment=1):
        active = self.active + increment
        if active >= len(self.modules):
            active = 0
        elif active < 0:
            active = len(self.modules) - 1
        self.active = active

    def on_click(self, button, **kwargs):
        """
        Capture scrollup and scorlldown to move in groups
        Pass everthing else to the module itself
        """
        if button in (4, 5):
            return super().on_click(button, **kwargs)
        else:
            activemodule = self.get_active_module()
            if not activemodule:
                return
            return activemodule.on_click(button, **kwargs)

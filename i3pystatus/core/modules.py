from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.threading import Manager
from i3pystatus.core.util import convert_position
from i3pystatus.core.command import execute
from i3pystatus.core.command import run_through_shell


class Module(SettingsBase):
    output = None
    position = 0

    settings = (
        ('on_leftclick', "Callback called on left click (see :ref:`callbacks`)"),
        ('on_rightclick', "Callback called on right click (see :ref:`callbacks`)"),
        ('on_upscroll', "Callback called on scrolling up (see :ref:`callbacks`)"),
        ('on_downscroll', "Callback called on scrolling down (see :ref:`callbacks`)"),
        ('hints', "Additional output blocks for module output (see :ref:`hints`)"),
    )

    on_leftclick = None
    on_rightclick = None
    on_upscroll = None
    on_downscroll = None

    hints = {"markup": "none"}

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""

    def inject(self, json):
        if self.output:
            if "name" not in self.output:
                self.output["name"] = self.__name__
            self.output["instance"] = str(id(self))
            if (self.output.get("color", "") or "").lower() == "#ffffff":
                del self.output["color"]
            if self.hints:
                for key, val in self.hints.items():
                    if key not in self.output:
                        self.output.update({key: val})
            if self.output.get("markup") == "pango":
                self.text_to_pango()

            json.insert(convert_position(self.position, json), self.output)

    def run(self):
        pass

    def on_click(self, button):
        """
        Maps a click event with its associated callback.

        Currently implemented events are:

        ===========  ================  =========
        Event        Callback setting  Button ID
        ===========  ================  =========
        Left click   on_leftclick      1
        Right click  on_rightclick     3
        Scroll up    on_upscroll       4
        Scroll down  on_downscroll     5
        ===========  ================  =========

        The action is determined by the nature (type and value) of the callback
        setting in the following order:

        1. If null callback (``None``), no action is taken.
        2. If it's a `python function`, call it and pass any additional
           arguments.
        3. If it's name of a `member method` of current module (string), call it
           and pass any additional arguments.
        4. If the name does not match with `member method` name execute program
           with such name.

        .. seealso:: :ref:`callbacks` for more information about
         callback settings and examples.

        :param button: The ID of button event received from i3bar.
        :type button: int
        :return: Returns ``True`` if a valid callback action was executed.
         ``False`` otherwise.
        :rtype: bool

        """

        def log_event(name, button, cb, args, action):
            msg = "{}: button={}, cb='{}', args={}, type='{}'".format(
                  name, button, cb, args, action)
            self.logger.debug(msg)

        def split_callback_and_args(cb):
            if isinstance(cb, list):
                return cb[0], cb[1:]
            else:
                return cb, []

        cb = None
        if button == 1:  # Left mouse button
            cb = self.on_leftclick
        elif button == 3:  # Right mouse button
            cb = self.on_rightclick
        elif button == 4:  # mouse wheel up
            cb = self.on_upscroll
        elif button == 5:  # mouse wheel down
            cb = self.on_downscroll
        else:
            log_event(self.__name__, button, None, None, "Unhandled button")
            return False

        if not cb:
            log_event(self.__name__, button, None, None, "No callback attached")
            return False
        else:
            cb, args = split_callback_and_args(cb)

        if callable(cb):
            log_event(self.__name__, button, cb, args, "Python callback")
            cb(self, *args)
        elif hasattr(self, cb):
            if cb is not "run":
                log_event(self.__name__, button, cb, args, "Member callback")
                getattr(self, cb)(*args)
        else:
            log_event(self.__name__, button, cb, args, "External command")
            execute(cb, detach=True)
        return True

    def move(self, position):
        self.position = position
        return self

    def text_to_pango(self):
        """
        Replaces all ampersands in `full_text` and `short_text` attributes of
        `self.output` with `&amp;`.

        It is called internally when pango markup is used.

        Can be called multiple times (`&amp;` won't change to `&amp;amp;`).
        """
        def replace(s):
            s = s.split("&")
            out = s[0]
            for i in range(len(s) - 1):
                if s[i + 1].startswith("amp;"):
                    out += "&" + s[i + 1]
                else:
                    out += "&amp;" + s[i + 1]
            return out

        if "full_text" in self.output.keys():
            self.output["full_text"] = replace(self.output["full_text"])
        if "short_text" in self.output.keys():
            self.output["short_text"] = replace(self.output["short_text"])


class IntervalModule(Module):
    settings = (
        ("interval", "interval in seconds between module updates"),
    )
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

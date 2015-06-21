import threading

from i3pystatus.core.io import StandaloneIO
from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.threading import Manager
from i3pystatus.core.util import convert_position
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
        Maps a click event (include mousewheel events) with its associated callback.
        It then triggers the callback depending on the nature (ie type) of
        the callback variable:
        1. if null callback, do nothing
        2. if it's a python function ()
        3. if it's the name of a method of the current module (string)

        To setup the callbacks, you can set the settings 'on_leftclick',
        'on_rightclick', 'on_upscroll', 'on_downscroll'.

        For instance, you can test with:
        ::

            status.register("clock",
                    format=[
                        ("Format 0",'Europe/London'),
                        ("%a %-d Format 1",'Europe/Dublin'),
                        "%a %-d %b %X format 2",
                        ("%a %-d %b %X format 3", 'Europe/Paris'),
                    ],
                    on_leftclick= ["urxvtc"] , # launch urxvtc on left click
                    on_rightclick= ["scroll_format", 2] , # update format by steps of 2
                    on_upscroll= [print, "hello world"] , # call python function print
                    log_level=logging.DEBUG,
                    )
        """

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
            self.logger.info("Button '%d' not handled yet." % (button))
            return False

        if not cb:
            self.logger.info("no cb attached")
            return False
        else:
            cb, args = split_callback_and_args(cb)
            self.logger.debug("cb=%s args=%s" % (cb, args))

        if callable(cb):
            cb(self)
        elif hasattr(self, cb):
            if cb is not "run":
                getattr(self, cb)(*args)
        else:
            run_through_shell(cb, *args)
        return True

    def on_refresh(self):
        """
        This method is always called after a click event or refresh triggered by
        SIGUSR1 signal.

        If module relies on internet acces or it's `run` method takes longer to
        execute this method shoul be overriden to refresh in background.
        Generally the `backgound_refresh` method should be used to refresh
        modules output without blocking other modules:

            .. code :: python

                def on_refresh(self):
                    self.background_refresh()

        For example :py:class:`.Network` module ignores refreshing completely
        becaue some of its computations rely on the `interval` setting.
        """
        self.run()

    def move(self, position):
        self.position = position
        return self

    def text_to_pango(self):
        """
        Replaces all ampersands in `"full_text"` and `"short_text"` in
        `self.output` with `&amp;`.

        Is called internally when pango markup is enabled.

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

    def background_refresh(self):
        """
        Runs modules `run` method in separate thread once and sends SIGUSR1
        signal afterwards to update the bar.
        """
        if getattr(self, "_refresh_thread", None) is None:
            self._refresh_thread = None

        # check if previous refresh is done
        if self._refresh_thread and not self._refresh_thread.is_alive():
            self._refresh_thread = None

        if not self._refresh_thread:
            def refresh_job(module):
                module.run()
                StandaloneIO.refresh_statusline()

            self._refresh_thread = threading.Thread(target=refresh_job, args=(self,))
            self._refresh_thread.start()


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

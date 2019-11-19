import inspect
import traceback

from i3pystatus.core.settings import SettingsBase
from i3pystatus.core.threading import Manager
from i3pystatus.core.util import (convert_position,
                                  MultiClickHandler)
from i3pystatus.core.command import execute


def is_method_of(method, object):
    """Decide whether ``method`` is contained within the MRO of ``object``."""
    if not callable(method) or not hasattr(method, "__name__"):
        return False
    if inspect.ismethod(method):
        return method.__self__ is object
    for cls in inspect.getmro(object.__class__):
        if cls.__dict__.get(method.__name__, None) is method:
            return True
    return False


class Module(SettingsBase):
    position = 0

    settings = (
        ('on_leftclick', "Callback called on left click (see :ref:`callbacks`)"),
        ('on_middleclick', "Callback called on middle click (see :ref:`callbacks`)"),
        ('on_rightclick', "Callback called on right click (see :ref:`callbacks`)"),
        ('on_upscroll', "Callback called on scrolling up (see :ref:`callbacks`)"),
        ('on_downscroll', "Callback called on scrolling down (see :ref:`callbacks`)"),
        ('on_doubleleftclick', "Callback called on double left click (see :ref:`callbacks`)"),
        ('on_doubleleftclick', "Callback called on double left click (see :ref:`callbacks`)"),
        ('on_doublemiddleclick', "Callback called on double middle click (see :ref:`callbacks`)"),
        ('on_doublerightclick', "Callback called on double right click (see :ref:`callbacks`)"),
        ('on_doubleupscroll', "Callback called on double scroll up (see :ref:`callbacks`)"),
        ('on_doubledownscroll', "Callback called on double scroll down (see :ref:`callbacks`)"),
        ('on_otherclick', "Callback called on other click (see :ref:`callbacks`)"),
        ('on_doubleotherclick', "Callback called on double other click (see :ref:`callbacks`)"),
        ('on_change', "Callback called when output is changed (see :ref:`callbacks`)"),
        ('multi_click_timeout', "Time (in seconds) before a single click is executed."),
        ('hints', "Additional output blocks for module output (see :ref:`hints`)"),
    )

    on_leftclick = None
    on_middleclick = None
    on_rightclick = None
    on_upscroll = None
    on_downscroll = None
    on_doubleleftclick = None
    on_doublemiddleclick = None
    on_doublerightclick = None
    on_doubleupscroll = None
    on_doubledownscroll = None

    on_otherclick = None
    on_change = None
    on_doubleotherclick = None

    multi_click_timeout = 0.25

    hints = {"markup": "none"}

    def __init__(self, *args, **kwargs):
        self._output = None
        super(Module, self).__init__(*args, **kwargs)
        self.__multi_click = MultiClickHandler(self.__button_callback_handler,
                                               self.multi_click_timeout)

    @property
    def output(self):
        return self._output

    @output.setter
    def output(self, value):
        self._output = value
        if self.on_change:
            self.on_change()

    def registered(self, status_handler):
        """Called when this module is registered with a status handler"""
        self.__status_handler = status_handler

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

    def send_output(self):
        """Send a status update with the current module output"""
        self.__status_handler.io.async_refresh()

    def __log_button_event(self, button, cb, args, action, **kwargs):
        msg = "{}: button={}, cb='{}', args={}, kwargs={}, type='{}'".format(
            self.__name__, button, cb, args, kwargs, action)
        self.logger.debug(msg)

    def __button_callback_handler(self, button, cb, **kwargs):

        def call_callback(cb, *args, **kwargs):
            # Recover the function if wrapped (with get_module for example)
            wrapped_cb = getattr(cb, "__wrapped__", None)
            if wrapped_cb:
                locals()["self"] = self  # Add self to the local stack frame
                tmp_cb = wrapped_cb
            else:
                tmp_cb = cb

            try:
                args_spec = inspect.getargspec(tmp_cb)
            except Exception:
                args_spec = inspect.ArgSpec([], None, None, None)

            # Remove all variables present in kwargs that are not used in the
            # callback, except if there is a keyword argument.
            if not args_spec.keywords:
                kwargs = {k: v for k, v in kwargs.items()
                          if k in args_spec.args}
            cb(*args, **kwargs)

        if not cb:
            self.__log_button_event(button, None, None,
                                    "No callback attached", **kwargs)
            return False

        if isinstance(cb, list):
            cb, args = (cb[0], cb[1:])
        else:
            args = []

        try:
            our_method = is_method_of(cb, self)
            if callable(cb) and not our_method:
                self.__log_button_event(button, cb, args,
                                        "Python callback", **kwargs)
                call_callback(cb, *args, **kwargs)
            elif our_method:
                self.__log_button_event(button, cb, args,
                                        "Method callback", **kwargs)
                call_callback(cb, self, *args, **kwargs)
            elif hasattr(self, cb):
                if cb != "run":
                    # CommandEndpoint already calls run() after every
                    # callback to instantly update any changed state due
                    # to the callback's actions.
                    self.__log_button_event(button, cb, args,
                                            "Member callback", **kwargs)
                    call_callback(getattr(self, cb), *args, **kwargs)
            else:
                self.__log_button_event(button, cb, args,
                                        "External command", **kwargs)

                if hasattr(self, "data"):
                    kwargs.update(self.data)

                args = [str(arg).format(**kwargs) for arg in args]
                cb = cb.format(**kwargs)
                execute(cb + " " + " ".join(args), detach=True)
        except Exception as e:
            self.logger.critical("Exception while processing button "
                                 "callback: {!r}".format(e))
            self.logger.critical(traceback.format_exc())

        # Notify status handler
        try:
            self.__status_handler.io.async_refresh()
        except:
            pass

    def on_click(self, button, **kwargs):
        """
        Maps a click event with its associated callback.

        Currently implemented events are:

        ============  ================  =========
        Event         Callback setting  Button ID
        ============  ================  =========
        Left click    on_leftclick      1
        Middle click  on_middleclick    2
        Right click   on_rightclick     3
        Scroll up     on_upscroll       4
        Scroll down   on_downscroll     5
        Others        on_otherclick     > 5
        ============  ================  =========

        The action is determined by the nature (type and value) of the callback
        setting in the following order:

        1. If null callback (``None``), no action is taken.
        2. If it's a `python function`, call it and pass any additional
           arguments.
        3. If it's name of a `member method` of current module (string), call
           it and pass any additional arguments.
        4. If the name does not match with `member method` name execute program
           with such name.

        .. seealso:: :ref:`callbacks` for more information about
         callback settings and examples.

        :param button: The ID of button event received from i3bar.
        :param kwargs: Further information received from i3bar like the
         positions of the mouse where the click occured.
        :return: Returns ``True`` if a valid callback action was executed.
         ``False`` otherwise.
        """

        actions = ['leftclick', 'middleclick', 'rightclick',
                   'upscroll', 'downscroll']
        try:
            action = actions[button - 1]
        except (TypeError, IndexError):
            self.__log_button_event(button, None, None, "Other button")
            action = "otherclick"

        m_click = self.__multi_click

        with m_click.lock:
            double = m_click.check_double(button)
            double_action = 'double%s' % action

            if double:
                action = double_action

            # Get callback function
            cb = getattr(self, 'on_%s' % action, None)

            double_handler = getattr(self, 'on_%s' % double_action, None)
            delay_execution = (not double and double_handler)

            if delay_execution:
                m_click.set_timer(button, cb, **kwargs)
            else:
                self.__button_callback_handler(button, cb, **kwargs)

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
        super(IntervalModule, self).registered(status_handler)
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

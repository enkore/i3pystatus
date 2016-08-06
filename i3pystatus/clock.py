import os
import locale
from datetime import datetime

from i3pystatus import IntervalModule


class Clock(IntervalModule):
    """
    This class shows a clock.

    .. note:: Optionally requires `pytz` for time zone data when using time
        zones other than local time.

    Format can be passed in four different ways:

    - single string, no timezone, just the strftime-format
    - one two-tuple, first is the format, second the timezone
    - list of strings - no timezones
    - list of two tuples, first is the format, second is timezone

    Use mousewheel to cycle between formats.

    For complete time format specification see:

    ::

        man strftime

    All available timezones are located in directory:

    ::

        /usr/share/zoneinfo/

    .. rubric:: Format examples

    ::

        # one format, local timezone
        format = '%a %b %-d %b %X'
        # multiple formats, local timezone
        format = [ '%a %b %-d %b %X', '%X' ]
        # one format, specified timezone
        format = ('%a %b %-d %b %X', 'Europe/Bratislava')
        # multiple formats, specified timezones
        format = [ ('%a %b %-d %b %X', 'America/New_York'), ('%X', 'Etc/GMT+9') ]

    """

    settings = (
        ("format", "`None` means to use the default, locale-dependent format."),
        ("color", "RGB hexadecimal code color specifier, default to #ffffff"),
    )
    format = None
    color = "#ffffff"
    interval = 1
    on_upscroll = ["scroll_format", 1]
    on_downscroll = ["scroll_format", -1]

    def init(self):
        env_lang = os.environ.get('LC_TIME', None)
        if env_lang is None:
            env_lang = os.environ.get('LANG', None)

        if env_lang is not None:
            if env_lang.find('.') != -1:
                lang = tuple(env_lang.split('.', 1))
            else:
                lang = (env_lang, None)
        else:
            lang = (None, None)

        if lang != locale.getlocale(locale.LC_TIME):
            # affects language of *.strftime() in whole program
            locale.setlocale(locale.LC_TIME, lang)

        if self.format is None:
            if lang[0] == 'en_US':
                # MDY format - United States of America
                self.format = ["%a %b %-d %X"]
            else:
                # DMY format - almost all other countries
                self.format = ["%a %-d %b %X"]

        elif isinstance(self.format, str) or isinstance(self.format, tuple):
            self.format = [self.format]
        self.format = [self._expand_format(fmt) for fmt in self.format]
        self.current_format_id = 0

    @staticmethod
    def _expand_format(fmt):
        if isinstance(fmt, tuple):
            if len(fmt) == 1:
                return (fmt[0], None)
            else:
                try:
                    from pytz import timezone
                except ImportError as e:
                    raise RuntimeError("Need `pytz` for timezone data") from e
                return (fmt[0], timezone(fmt[1]))
        return (fmt, None)

    def run(self):
        time = datetime.now(self.format[self.current_format_id][1])

        self.output = {
            "full_text": time.strftime(self.format[self.current_format_id][0]),
            "color": self.color,
            "urgent": False,
        }

    def scroll_format(self, step=1):
        self.current_format_id = (self.current_format_id + step) % len(self.format)

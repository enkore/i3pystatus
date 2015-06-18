import os
import locale
import time

from i3pystatus import IntervalModule


class Clock(IntervalModule):
    """
    This class shows a clock.

    format can be passed in four different ways:

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
    current_format_id = 0
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
            # affects time.strftime() in whole program
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

        self.format = self.expand_formats(self.format)

    @staticmethod
    def expand_formats(formats):
        def expand_format(format_):
            if isinstance(format_, tuple):
                # check if timezone exists (man tzset)
                if len(format_) > 1 and os.path.isfile('/usr/share/zoneinfo/' + format_[1]):
                    return (format_[0], format_[1])
                else:
                    return (format_[0], time.tzname[0])
            return (format_, time.tzname[0])

        return [expand_format(format_) for format_ in formats]

    def run(self):
        # set timezone
        if time.tzname[0] is not self.format[self.current_format_id][1]:
            os.environ.putenv('TZ', self.format[self.current_format_id][1])
            time.tzset()

        self.output = {
            "full_text": time.strftime(self.format[self.current_format_id][0]),
            "color": self.color,
            "urgent": False,
        }

    def scroll_format(self, step=1):
        self.current_format_id = (self.current_format_id + step) % len(self.format)

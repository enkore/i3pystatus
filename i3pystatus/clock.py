#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import locale
import datetime

from i3pystatus import IntervalModule


class Clock(IntervalModule):
    """
    This class shows a clock
    """

    settings = (
        ("format", "list of tuple (stftime format string, optional timezone), `None` means to use the default, locale-dependent format. Can cycle between formats with mousewheel"),
        ("color", "RGB hexadecimal code color specifier, default to #ffffff, set to `i3Bar` to use i3 bar default"),
    )
    format = None
    color = "#ffffff"
    interval = 1
    current_format_id = 0

    def init(self):
        if self.format is None:
            lang = os.environ.get('LANG', None)
            if lang:
                locale.setlocale(locale.LC_ALL, lang)
            lang = locale.getlocale()[0]
            if lang == 'en_US':
                # MDY format - United States of America
                self.format = ["%a %b %-d %X"]
            else:
                # DMY format - almost all other countries
                self.format = ["%a %-d %b %X"]

        elif isinstance(self.format, str):
            self.format = [self.format]

        self.format = self.expand_formats(self.format)

    @staticmethod
    def expand_formats(formats):
        def expand_format(format_):
            if isinstance(format_, tuple):
                return (format_[0], format_[1] if len(format_) > 1 else None)
            return (format_, None)

        return [expand_format(format_) for format_ in formats]

    def run(self):
        # Safest way is to work from utc and localize afterwards
        if self.format[self.current_format_id][1]:
            try:
                import pytz
            except ImportError as e:
                raise RuntimeError("Need pytz for timezones") from e
            utc_dt = pytz.utc.localize(datetime.datetime.utcnow())
            tz = pytz.timezone(self.format[self.current_format_id][1])
            dt = tz.normalize(utc_dt.astimezone(tz))
        else:
            dt = datetime.datetime.now()

        output = dt.strftime(self.format[self.current_format_id][0])

        self.output = {
            "full_text": output,
            "urgent": False,
        }
        if self.color != "i3Bar":
            self.output["color"] = self.color

    def next_format(self,step=1):
        self.current_format_id = (self.current_format_id + step) % len(self.format)

    def previous_format(self):
        self.current_format_id = (self.current_format_id + 1) % len(self.format)

    def on_upscroll(self):
        self.next_format()

    def on_downscroll(self):
        self.previous_format()

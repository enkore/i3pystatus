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
        ("format", "stftime format string, `None` means to use the default, locale-dependent format"),
        ("color", "RGB hexadecimal code color specifier, default to #ffffff, set to `i3Bar` to use i3 bar default"),
    )
    format = None
    color = "#ffffff"
    interval = 1

    def init(self):
        if self.format is None:
            lang = os.environ.get('LANG', None)
            if lang:
                locale.setlocale(locale.LC_ALL, lang)
            lang = locale.getlocale()[0]
            if lang == 'en_US':
                # MDY format - United States of America
                self.format = "%a %b %-d %X"
            else:
                # DMY format - almost all other countries
                self.format = "%a %-d %b %X"

    def run(self):
        self.output = {
            "full_text": datetime.datetime.now().strftime(self.format),
            "urgent": False,
        }
        if self.color != "i3Bar":
            self.output["color"] = self.color

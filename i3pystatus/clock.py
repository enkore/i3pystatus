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
        ("format", "list of stftime format string, `None` means to use the default, locale-dependent format. Can cycle between formats with mousewheel"),
        ("color", "RGB hexadecimal code color specifier, default to #ffffff, set to `i3Bar` to use i3 bar default"),
    )
    format = None
    color = "#ffffff"
    interval = 1
    currentFormatId = 0

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

        elif isinstance(self.format,str):
            self.format=[self.format]

    def run(self):
        self.output = {
            # todo find local
            "full_text": datetime.datetime.now().strftime(self.format[self.currentFormatId]),
            "urgent": False,
        }
        if self.color != "i3Bar":
            self.output["color"] = self.color
            

    def on_upscroll(self):
        self.currentFormatId = (self.currentFormatId + 1)% len(self.format)

    def on_downscroll(self):
        self.currentFormatId = (self.currentFormatId - 1)% len(self.format)

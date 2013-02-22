#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, locale, datetime

from i3pystatus import IntervalModule

class Clock(IntervalModule):
    """ 
    This class shows a clock
    """

    settings = ("format",)
    format = None

    def init(self):
        lang = os.environ.get('LANG', None)
        if lang:
            locale.setlocale(locale.LC_ALL, lang)
        if self.format is not None:
            lang = locale.getlocale()[0]
            if lang == 'en_US':
                # MDY format - United States of America
                self.format = "%a %b %-d %X"
            else:
                # DMY format - almost all other countries
                self.format = "%a %-d %b %X"

    def run(self):
        full_text = datetime.datetime.now().strftime(self.format)
        self.output = {
            "full_text": full_text,
            "name": "pyclock",
            "urgent": False,
            "color": "#ffffff"
        }
